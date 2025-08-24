"""
Binance REST API Client

Professional REST API client with comprehensive error handling,
rate limiting, and security features for crypto trading.
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlencode
import ssl

from .config import ConfigManager
from .security import SecurityManager
from .rate_limiter import RateLimitManager, RateLimitType

logger = logging.getLogger(__name__)


class BinanceAPIError(Exception):
	"""Binance API specific error."""

	def __init__(
		self,
		message: str,
		status_code: Optional[int] = None,
		error_code: Optional[int] = None,
	):
		super().__init__(message)
		self.status_code = status_code
		self.error_code = error_code


class BinanceClient:
	"""Professional Binance REST API client."""

	# API endpoint weights (from Binance documentation)
	ENDPOINT_WEIGHTS = {
		'/api/v3/exchangeInfo': 10,
		'/api/v3/depth': 5,  # Default for limit <= 100
		'/api/v3/trades': 1,
		'/api/v3/historicalTrades': 5,
		'/api/v3/aggTrades': 1,
		'/api/v3/klines': 1,
		'/api/v3/avgPrice': 1,
		'/api/v3/ticker/24hr': 1,  # Single symbol
		'/api/v3/ticker/price': 1,  # Single symbol
		'/api/v3/ticker/bookTicker': 1,  # Single symbol
		'/api/v3/account': 10,
		'/api/v3/myTrades': 10,
		'/api/v3/order': 1,  # GET
		'/api/v3/openOrders': 3,  # Single symbol
		'/api/v3/allOrders': 10,
		# Order operations
		'/api/v3/order/test': 1,  # Test order
		'/api/v3/order': 1,  # POST (place order)
	}

	def __init__(self, config_manager: Optional[ConfigManager] = None):
		"""Initialize Binance client.

		Args:
		    config_manager: Configuration manager instance
		"""
		self.config = config_manager or ConfigManager()
		self.config.validate_config()

		# Initialize security manager
		credentials = self.config.get_api_credentials()
		self.security = SecurityManager(
			api_key=credentials['api_key'],
			api_secret=credentials.get('api_secret'),
			private_key_path=credentials.get('private_key_path'),
		)

		# Initialize rate limiting
		self.rate_limiter = RateLimitManager()

		# HTTP session
		self._session: Optional[aiohttp.ClientSession] = None

		# Connection settings
		self._timeout = aiohttp.ClientTimeout(total=30, connect=10)

		# Create SSL context with proper configuration for testnet
		ssl_context = ssl.create_default_context()
		if self.config.is_testnet() or self.config.is_paper_trading():
			# For testnet, use a more lenient SSL configuration due to known certificate issues
			ssl_context.check_hostname = False
			ssl_context.verify_mode = ssl.CERT_NONE
			logger.warning(
				'SSL verification disabled for testnet/paper trading environment'
			)
		else:
			# For mainnet, keep strict SSL verification for security
			logger.info('Using strict SSL verification for mainnet environment')

		self._connector = aiohttp.TCPConnector(
			limit=100,
			limit_per_host=10,
			keepalive_timeout=30,
			ssl=ssl_context,
		)

		logger.info(f'BinanceClient initialized for {self.config.environment.value}')

	async def __aenter__(self):
		"""Async context manager entry."""
		await self._ensure_session()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit."""
		await self.close()

	async def _ensure_session(self) -> None:
		"""Ensure HTTP session is available."""
		if self._session is None or self._session.closed:
			self._session = aiohttp.ClientSession(
				timeout=self._timeout,
				connector=self._connector,
				headers={'User-Agent': 'crypto_agents/1.0.0'},
			)

	async def close(self) -> None:
		"""Close HTTP session."""
		if self._session and not self._session.closed:
			await self._session.close()
			self._session = None

	def _get_endpoint_weight(self, endpoint: str, params: Optional[Dict] = None) -> int:
		"""Get API weight for endpoint.

		Args:
		    endpoint: API endpoint path
		    params: Request parameters

		Returns:
		    API weight for the endpoint
		"""
		base_weight = self.ENDPOINT_WEIGHTS.get(endpoint, 1)

		# Adjust weight based on parameters
		if endpoint == '/api/v3/depth' and params:
			limit = params.get('limit', 100)
			if limit <= 100:
				return 5
			elif limit <= 500:
				return 25
			elif limit <= 1000:
				return 50
			else:
				return 50

		elif endpoint == '/api/v3/ticker/24hr' and not (
			params and params.get('symbol')
		):
			return 40  # All symbols

		elif endpoint == '/api/v3/ticker/price' and not (
			params and params.get('symbol')
		):
			return 2  # All symbols

		elif endpoint == '/api/v3/ticker/bookTicker' and not (
			params and params.get('symbol')
		):
			return 2  # All symbols

		elif endpoint == '/api/v3/openOrders' and not (params and params.get('symbol')):
			return 40  # All symbols

		return base_weight

	async def _request(
		self,
		method: str,
		endpoint: str,
		params: Optional[Dict[str, Any]] = None,
		signed: bool = False,
		timeout: Optional[float] = None,
	) -> Dict[str, Any]:
		"""Make HTTP request to Binance API.

		Args:
		    method: HTTP method (GET, POST, etc.)
		    endpoint: API endpoint path
		    params: Request parameters
		    signed: Whether request needs to be signed
		    timeout: Request timeout override

		Returns:
		    API response data

		Raises:
		    BinanceAPIError: If API request fails
		"""
		await self._ensure_session()

		if params is None:
			params = {}

		# Check rate limits
		endpoint_weight = self._get_endpoint_weight(endpoint, params)
		limit_type = (
			RateLimitType.ORDERS
			if 'order' in endpoint
			else RateLimitType.REQUEST_WEIGHT
		)

		if not self.rate_limiter.acquire(endpoint_weight, limit_type):
			raise BinanceAPIError('Rate limit exceeded, request denied')

		# Prepare request
		url = f'{self.config.endpoints.rest_base}{endpoint}'
		headers = self.security.get_headers(signed)

		# Handle different request methods
		request_kwargs = {'timeout': timeout or self._timeout, 'headers': headers}

		if method.upper() == 'GET':
			if signed:
				params = self.security.create_signed_params(params)
			if params:
				url += '?' + urlencode(params)
		else:
			# For POST requests, we need to be careful about signature generation
			if signed:
				params = self.security.create_signed_params(params)
			request_kwargs['data'] = urlencode(params) if params else None
			headers['Content-Type'] = 'application/x-www-form-urlencoded'

		# Make request
		try:
			logger.debug(
				f'Making {method} request to {endpoint} (weight: {endpoint_weight})'
			)
			async with self._session.request(method, url, **request_kwargs) as response:
				# Update rate limits from response headers
				self.rate_limiter.update_from_response_headers(dict(response.headers))

				# Handle response
				response_text = await response.text()

				if response.status == 200:
					try:
						return json.loads(response_text)
					except json.JSONDecodeError:
						raise BinanceAPIError(f'Invalid JSON response: {response_text}')

				# Handle error responses
				elif response.status in [429, 418]:
					wait_time = self.rate_limiter.handle_rate_limit_error(
						response.status, dict(response.headers)
					)
					raise BinanceAPIError(
						f'Rate limit error: {response_text}',
						status_code=response.status,
					)

				else:
					# Try to parse error response
					try:
						error_data = json.loads(response_text)
						error_msg = error_data.get('msg', response_text)
						error_code = error_data.get('code')
					except json.JSONDecodeError:
						error_msg = response_text
						error_code = None

					raise BinanceAPIError(
						f'API error: {error_msg}',
						status_code=response.status,
						error_code=error_code,
					)

		except aiohttp.ClientError as e:
			raise BinanceAPIError(f'HTTP client error: {str(e)}')
		except asyncio.TimeoutError:
			raise BinanceAPIError('Request timeout')

	# Market Data Endpoints

	async def get_server_time(self) -> Dict[str, Any]:
		"""Get server time.

		Returns:
		    Server time information
		"""
		return await self._request('GET', '/api/v3/time')

	async def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
		"""Get exchange information.

		Args:
		    symbol: Optional symbol to get info for

		Returns:
		    Exchange information
		"""
		params = {'symbol': symbol} if symbol else {}
		return await self._request('GET', '/api/v3/exchangeInfo', params)

	async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
		"""Get order book depth.

		Args:
		    symbol: Trading pair symbol (e.g., 'BTCUSDT')
		    limit: Number of entries to return (5, 10, 20, 50, 100, 500, 1000, 5000)

		Returns:
		    Order book data
		"""
		params = {'symbol': symbol, 'limit': limit}
		return await self._request('GET', '/api/v3/depth', params)

	async def get_recent_trades(
		self, symbol: str, limit: int = 500
	) -> List[Dict[str, Any]]:
		"""Get recent trades.

		Args:
		    symbol: Trading pair symbol
		    limit: Number of trades to return (max 1000)

		Returns:
		    List of recent trades
		"""
		params = {'symbol': symbol, 'limit': limit}
		return await self._request('GET', '/api/v3/trades', params)

	async def get_klines(
		self,
		symbol: str,
		interval: str,
		start_time: Optional[int] = None,
		end_time: Optional[int] = None,
		limit: int = 500,
	) -> List[List[Union[str, float]]]:
		"""Get kline/candlestick data.

		Args:
		    symbol: Trading pair symbol
		    interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
		    start_time: Start time timestamp
		    end_time: End time timestamp
		    limit: Number of klines to return (max 1000)

		Returns:
		    List of kline data
		"""
		params = {'symbol': symbol, 'interval': interval, 'limit': limit}

		if start_time:
			params['startTime'] = start_time
		if end_time:
			params['endTime'] = end_time

		return await self._request('GET', '/api/v3/klines', params)

	async def get_24hr_ticker(
		self, symbol: Optional[str] = None
	) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
		"""Get 24hr ticker price change statistics.

		Args:
		    symbol: Trading pair symbol (if None, returns all symbols)

		Returns:
		    Ticker data
		"""
		params = {'symbol': symbol} if symbol else {}
		return await self._request('GET', '/api/v3/ticker/24hr', params)

	async def get_symbol_price(
		self, symbol: Optional[str] = None
	) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
		"""Get latest price for symbol(s).

		Args:
		    symbol: Trading pair symbol (if None, returns all symbols)

		Returns:
		    Price data
		"""
		params = {'symbol': symbol} if symbol else {}
		return await self._request('GET', '/api/v3/ticker/price', params)

	# Account Endpoints (Signed)

	async def get_account_info(self) -> Dict[str, Any]:
		"""Get account information.

		Returns:
		    Account information including balances
		"""
		return await self._request('GET', '/api/v3/account', signed=True)

	async def get_open_orders(
		self, symbol: Optional[str] = None
	) -> List[Dict[str, Any]]:
		"""Get open orders.

		Args:
		    symbol: Trading pair symbol (if None, returns all symbols)

		Returns:
		    List of open orders
		"""
		params = {'symbol': symbol} if symbol else {}
		return await self._request('GET', '/api/v3/openOrders', params, signed=True)

	async def get_all_orders(
		self, symbol: str, limit: int = 500
	) -> List[Dict[str, Any]]:
		"""Get all orders for a symbol.

		Args:
		    symbol: Trading pair symbol
		    limit: Number of orders to return (max 1000)

		Returns:
		    List of orders
		"""
		params = {'symbol': symbol, 'limit': limit}
		return await self._request('GET', '/api/v3/allOrders', params, signed=True)

	async def get_order(
		self,
		symbol: str,
		order_id: Optional[int] = None,
		orig_client_order_id: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Get order details.

		Args:
		    symbol: Trading pair symbol
		    order_id: Order ID
		    orig_client_order_id: Original client order ID

		Returns:
		    Order details
		"""
		params = {'symbol': symbol}

		if order_id:
			params['orderId'] = order_id
		elif orig_client_order_id:
			params['origClientOrderId'] = orig_client_order_id
		else:
			raise ValueError('Either order_id or orig_client_order_id must be provided')

		return await self._request('GET', '/api/v3/order', params, signed=True)

	# Trading Endpoints (Signed)

	async def place_test_order(
		self,
		symbol: str,
		side: str,
		order_type: str,
		quantity: float,
		price: Optional[float] = None,
		time_in_force: str = 'GTC',
		client_order_id: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Place a test order (no actual trade).

		Args:
		    symbol: Trading pair symbol
		    side: Order side (BUY or SELL)
		    order_type: Order type (MARKET, LIMIT, etc.)
		    quantity: Order quantity
		    price: Order price (required for LIMIT orders)
		    time_in_force: Time in force (GTC, IOC, FOK)
		    client_order_id: Client order ID

		Returns:
		    Test order response
		"""
		params = {
			'symbol': symbol,
			'side': side.upper(),
			'type': order_type.upper(),
			'quantity': str(quantity),
		}

		# Only add timeInForce for order types that require it
		# MARKET orders don't need timeInForce
		if order_type.upper() not in ['MARKET']:
			params['timeInForce'] = time_in_force

		if price:
			params['price'] = str(price)

		if client_order_id:
			params['newClientOrderId'] = client_order_id
		else:
			params['newClientOrderId'] = self.security.generate_client_order_id()

		# Validate order data
		self.security.validate_order_data(params)

		return await self._request('POST', '/api/v3/order/test', params, signed=True)

	async def place_order(
		self,
		symbol: str,
		side: str,
		order_type: str,
		quantity: float,
		price: Optional[float] = None,
		time_in_force: str = 'GTC',
		client_order_id: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Place a real order.

		Args:
		    symbol: Trading pair symbol
		    side: Order side (BUY or SELL)
		    order_type: Order type (MARKET, LIMIT, etc.)
		    quantity: Order quantity
		    price: Order price (required for LIMIT orders)
		    time_in_force: Time in force (GTC, IOC, FOK)
		    client_order_id: Client order ID

		Returns:
		    Order response
		"""
		# In paper trading mode, use test orders
		if self.config.is_paper_trading():
			logger.info('Paper trading mode: placing test order instead of real order')
			return await self.place_test_order(
				symbol,
				side,
				order_type,
				quantity,
				price,
				time_in_force,
				client_order_id,
			)

		params = {
			'symbol': symbol,
			'side': side.upper(),
			'type': order_type.upper(),
			'quantity': str(quantity),
		}

		# Only add timeInForce for order types that require it
		# MARKET orders don't need timeInForce
		if order_type.upper() not in ['MARKET']:
			params['timeInForce'] = time_in_force

		if price:
			params['price'] = str(price)

		if client_order_id:
			params['newClientOrderId'] = client_order_id
		else:
			params['newClientOrderId'] = self.security.generate_client_order_id()

		# Validate order data
		self.security.validate_order_data(params)

		logger.info(
			f'Placing {side} order for {quantity} {symbol} at {price or "market"}'
		)
		return await self._request('POST', '/api/v3/order', params, signed=True)

	async def cancel_order(
		self,
		symbol: str,
		order_id: Optional[int] = None,
		orig_client_order_id: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Cancel an order.

		Args:
		    symbol: Trading pair symbol
		    order_id: Order ID
		    orig_client_order_id: Original client order ID

		Returns:
		    Cancel response
		"""
		params = {'symbol': symbol}

		if order_id:
			params['orderId'] = order_id
		elif orig_client_order_id:
			params['origClientOrderId'] = orig_client_order_id
		else:
			raise ValueError('Either order_id or orig_client_order_id must be provided')

		return await self._request('DELETE', '/api/v3/order', params, signed=True)

	# Utility Methods

	def get_status(self) -> Dict[str, Any]:
		"""Get client status information.

		Returns:
		    Status information
		"""
		return {
			'environment': self.config.environment.value,
			'is_paper_trading': self.config.is_paper_trading(),
			'rate_limits': self.rate_limiter.get_status(),
			'request_stats': self.rate_limiter.get_request_stats(),
			'config': self.config.to_dict(),
		}
