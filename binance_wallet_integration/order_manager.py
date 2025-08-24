"""
Order Management System for Binance Integration

Professional order management with risk controls, validation,
and integration with the crypto_agents trading system.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN

from .client import BinanceClient
from .config import ConfigManager

logger = logging.getLogger(__name__)


class OrderSide(Enum):
	"""Order side enumeration."""

	BUY = 'BUY'
	SELL = 'SELL'


class OrderType(Enum):
	"""Order type enumeration."""

	MARKET = 'MARKET'
	LIMIT = 'LIMIT'
	STOP_LOSS = 'STOP_LOSS'
	STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
	TAKE_PROFIT = 'TAKE_PROFIT'
	TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'


class OrderStatus(Enum):
	"""Order status enumeration."""

	PENDING = 'PENDING'
	NEW = 'NEW'
	PARTIALLY_FILLED = 'PARTIALLY_FILLED'
	FILLED = 'FILLED'
	CANCELED = 'CANCELED'
	PENDING_CANCEL = 'PENDING_CANCEL'
	REJECTED = 'REJECTED'
	EXPIRED = 'EXPIRED'


@dataclass
class OrderRequest:
	"""Order request structure."""

	symbol: str
	side: OrderSide
	order_type: OrderType
	quantity: float
	price: Optional[float] = None
	stop_price: Optional[float] = None
	time_in_force: str = 'GTC'
	client_order_id: Optional[str] = None

	# Risk management fields
	max_slippage: float = 0.005  # 0.5%
	timeout_seconds: int = 30


@dataclass
class OrderResult:
	"""Order execution result."""

	success: bool
	order_id: Optional[str] = None
	client_order_id: Optional[str] = None
	status: Optional[OrderStatus] = None
	filled_quantity: float = 0.0
	filled_price: float = 0.0
	commission: float = 0.0
	commission_asset: str = ''
	error_message: Optional[str] = None
	raw_response: Optional[Dict[str, Any]] = None


@dataclass
class RiskLimits:
	"""Risk management limits."""

	max_position_size_usd: float = 10000.0
	max_order_size_usd: float = 5000.0
	max_daily_volume_usd: float = 50000.0
	max_slippage_tolerance: float = 0.01  # 1%
	min_order_size_usd: float = 10.0

	# Daily tracking
	daily_volume_usd: float = 0.0
	daily_reset_time: float = field(default_factory=lambda: time.time())


class OrderManager:
	"""Professional order management system."""

	def __init__(
		self,
		binance_client: BinanceClient,
		config_manager: Optional[ConfigManager] = None,
	):
		"""Initialize order manager.

		Args:
		    binance_client: Binance API client
		    config_manager: Configuration manager
		"""
		self.client = binance_client
		self.config = config_manager or ConfigManager()

		# Risk management
		self.risk_limits = RiskLimits(
			max_position_size_usd=self.config.trading_config.max_position_size_usd,
			max_order_size_usd=self.config.trading_config.max_position_size_usd * 0.5,
			min_order_size_usd=self.config.trading_config.min_order_size_usd,
			max_slippage_tolerance=self.config.trading_config.slippage_tolerance * 2,
		)

		# Order tracking
		self._active_orders: Dict[str, Dict[str, Any]] = {}
		self._order_history: List[OrderResult] = []

		# Symbol info cache
		self._symbol_info: Dict[str, Dict[str, Any]] = {}

		logger.info('OrderManager initialized')

	async def initialize(self) -> None:
		"""Initialize order manager (fetch symbol info, etc.)."""
		try:
			# Fetch exchange info
			exchange_info = await self.client.get_exchange_info()

			# Cache symbol information
			for symbol_info in exchange_info.get('symbols', []):
				symbol = symbol_info['symbol']
				self._symbol_info[symbol] = symbol_info

			logger.info(f'Loaded info for {len(self._symbol_info)} symbols')

		except Exception as e:
			logger.error(f'Failed to initialize OrderManager: {e}')
			raise

	def _get_symbol_info(self, symbol: str) -> Dict[str, Any]:
		"""Get symbol trading information.

		Args:
		    symbol: Trading pair symbol

		Returns:
		    Symbol information

		Raises:
		    ValueError: If symbol not found
		"""
		if symbol not in self._symbol_info:
			raise ValueError(f'Symbol {symbol} not found or not supported')

		return self._symbol_info[symbol]

	def _get_lot_size_filter(self, symbol: str) -> Dict[str, Any]:
		"""Get lot size filter for symbol.

		Args:
		    symbol: Trading pair symbol

		Returns:
		    Lot size filter information
		"""
		symbol_info = self._get_symbol_info(symbol)

		for filter_info in symbol_info.get('filters', []):
			if filter_info['filterType'] == 'LOT_SIZE':
				return filter_info

		raise ValueError(f'LOT_SIZE filter not found for {symbol}')

	def _get_price_filter(self, symbol: str) -> Dict[str, Any]:
		"""Get price filter for symbol.

		Args:
		    symbol: Trading pair symbol

		Returns:
		    Price filter information
		"""
		symbol_info = self._get_symbol_info(symbol)

		for filter_info in symbol_info.get('filters', []):
			if filter_info['filterType'] == 'PRICE_FILTER':
				return filter_info

		raise ValueError(f'PRICE_FILTER not found for {symbol}')

	def _get_min_notional_filter(self, symbol: str) -> Dict[str, Any]:
		"""Get minimum notional filter for symbol.

		Args:
		    symbol: Trading pair symbol

		Returns:
		    Min notional filter information
		"""
		symbol_info = self._get_symbol_info(symbol)

		for filter_info in symbol_info.get('filters', []):
			if filter_info['filterType'] == 'MIN_NOTIONAL':
				return filter_info

		raise ValueError(f'MIN_NOTIONAL filter not found for {symbol}')

	def _format_quantity(self, symbol: str, quantity: float) -> str:
		"""Format quantity according to symbol's lot size rules.

		Args:
		    symbol: Trading pair symbol
		    quantity: Raw quantity

		Returns:
		    Formatted quantity string
		"""
		lot_size = self._get_lot_size_filter(symbol)
		step_size = float(lot_size['stepSize'])

		# Round down to step size
		decimal_places = str(step_size)[::-1].find('.')
		if decimal_places == -1:
			decimal_places = 0

		quantity_decimal = Decimal(str(quantity))
		step_decimal = Decimal(str(step_size))

		# Round down to nearest step
		formatted_quantity = quantity_decimal.quantize(
			step_decimal, rounding=ROUND_DOWN
		)

		return str(formatted_quantity)

	def _format_price(self, symbol: str, price: float) -> str:
		"""Format price according to symbol's price filter rules.

		Args:
		    symbol: Trading pair symbol
		    price: Raw price

		Returns:
		    Formatted price string
		"""
		price_filter = self._get_price_filter(symbol)
		tick_size = float(price_filter['tickSize'])

		# Round to tick size
		decimal_places = str(tick_size)[::-1].find('.')
		if decimal_places == -1:
			decimal_places = 0

		price_decimal = Decimal(str(price))
		tick_decimal = Decimal(str(tick_size))

		formatted_price = price_decimal.quantize(tick_decimal)

		return str(formatted_price)

	async def _get_current_price(self, symbol: str) -> float:
		"""Get current market price for symbol.

		Args:
		    symbol: Trading pair symbol

		Returns:
		    Current price
		"""
		try:
			ticker = await self.client.get_symbol_price(symbol)
			return float(ticker['price'])
		except Exception as e:
			logger.error(f'Failed to get current price for {symbol}: {e}')
			raise

	def _validate_order_request(self, request: OrderRequest) -> None:
		"""Validate order request.

		Args:
		    request: Order request to validate

		Raises:
		    ValueError: If validation fails
		"""
		# Check symbol exists
		if request.symbol not in self._symbol_info:
			raise ValueError(f'Symbol {request.symbol} not supported')

		# Validate quantity
		if request.quantity <= 0:
			raise ValueError('Quantity must be positive')

		# Validate price for limit orders
		if request.order_type in [
			OrderType.LIMIT,
			OrderType.STOP_LOSS_LIMIT,
			OrderType.TAKE_PROFIT_LIMIT,
		]:
			if not request.price or request.price <= 0:
				raise ValueError(
					f'Price required for {request.order_type.value} orders'
				)

		# Check lot size
		lot_size = self._get_lot_size_filter(request.symbol)
		min_qty = float(lot_size['minQty'])
		max_qty = float(lot_size['maxQty'])

		if request.quantity < min_qty:
			raise ValueError(f'Quantity {request.quantity} below minimum {min_qty}')

		if request.quantity > max_qty:
			raise ValueError(f'Quantity {request.quantity} above maximum {max_qty}')

	async def _check_risk_limits(self, request: OrderRequest) -> None:
		"""Check risk management limits.

		Args:
		    request: Order request to check

		Raises:
		    ValueError: If risk limits exceeded
		"""
		# Get current price for notional calculation
		current_price = await self._get_current_price(request.symbol)
		order_notional = request.quantity * current_price

		# Check minimum order size
		if order_notional < self.risk_limits.min_order_size_usd:
			raise ValueError(
				f'Order size ${order_notional:.2f} below minimum ${self.risk_limits.min_order_size_usd}'
			)

		# Check maximum order size
		if order_notional > self.risk_limits.max_order_size_usd:
			raise ValueError(
				f'Order size ${order_notional:.2f} exceeds maximum ${self.risk_limits.max_order_size_usd}'
			)

		# Check daily volume limit
		current_time = time.time()
		if current_time - self.risk_limits.daily_reset_time > 86400:  # 24 hours
			self.risk_limits.daily_volume_usd = 0
			self.risk_limits.daily_reset_time = current_time

		if (
			self.risk_limits.daily_volume_usd + order_notional
			> self.risk_limits.max_daily_volume_usd
		):
			raise ValueError(
				f'Daily volume limit would be exceeded: ${self.risk_limits.daily_volume_usd + order_notional:.2f} > ${self.risk_limits.max_daily_volume_usd}'
			)

		# Check exchange minimum notional
		try:
			min_notional = self._get_min_notional_filter(request.symbol)
			min_notional_value = float(min_notional['minNotional'])

			if order_notional < min_notional_value:
				raise ValueError(
					f'Order notional ${order_notional:.2f} below exchange minimum ${min_notional_value}'
				)
		except ValueError:
			# Some symbols might not have MIN_NOTIONAL filter
			pass

	async def place_order(
		self, request: OrderRequest, dry_run: bool = False
	) -> OrderResult:
		"""Place an order with full validation and risk management.

		Args:
		    request: Order request
		    dry_run: If True, validate but don't execute

		Returns:
		    Order execution result
		"""
		try:
			# Validate request
			self._validate_order_request(request)

			# Check risk limits
			await self._check_risk_limits(request)

			# Format quantities and prices
			formatted_quantity = self._format_quantity(request.symbol, request.quantity)
			formatted_price = None

			if request.price:
				formatted_price = self._format_price(request.symbol, request.price)

			if dry_run:
				logger.info(
					f'DRY RUN: {request.side.value} {formatted_quantity} {request.symbol} at {formatted_price or "MARKET"}'
				)
				return OrderResult(
					success=True,
					client_order_id='DRY_RUN',
					status=OrderStatus.FILLED,
					filled_quantity=float(formatted_quantity),
					filled_price=float(formatted_price)
					if formatted_price
					else await self._get_current_price(request.symbol),
				)

			# Place the order
			if self.config.is_paper_trading():
				# Use test order endpoint
				response = await self.client.place_test_order(
					symbol=request.symbol,
					side=request.side.value,
					order_type=request.order_type.value,
					quantity=float(formatted_quantity),
					price=float(formatted_price) if formatted_price else None,
					time_in_force=request.time_in_force,
					client_order_id=request.client_order_id,
				)

				# Test orders return empty response on success
				result = OrderResult(
					success=True,
					client_order_id=request.client_order_id,
					status=OrderStatus.FILLED,
					filled_quantity=float(formatted_quantity),
					filled_price=float(formatted_price)
					if formatted_price
					else await self._get_current_price(request.symbol),
					raw_response=response,
				)

			else:
				# Place real order
				response = await self.client.place_order(
					symbol=request.symbol,
					side=request.side.value,
					order_type=request.order_type.value,
					quantity=float(formatted_quantity),
					price=float(formatted_price) if formatted_price else None,
					time_in_force=request.time_in_force,
					client_order_id=request.client_order_id,
				)

				result = OrderResult(
					success=True,
					order_id=str(response.get('orderId')),
					client_order_id=response.get('clientOrderId'),
					status=OrderStatus(response.get('status', 'NEW')),
					filled_quantity=float(response.get('executedQty', 0)),
					filled_price=float(response.get('price', 0))
					if response.get('price')
					else 0,
					raw_response=response,
				)

				# Track active order
				if result.order_id:
					self._active_orders[result.order_id] = {
						'request': request,
						'result': result,
						'timestamp': time.time(),
					}

			# Update daily volume
			order_notional = result.filled_quantity * result.filled_price
			if result.filled_quantity > 0:
				self.risk_limits.daily_volume_usd += order_notional

			# Add to history
			self._order_history.append(result)

			logger.info(
				f'Order placed successfully: {request.side.value} {result.filled_quantity} {request.symbol}'
			)
			return result

		except Exception as e:
			logger.error(f'Failed to place order: {e}')
			return OrderResult(success=False, error_message=str(e))

	async def cancel_order(
		self,
		symbol: str,
		order_id: Optional[str] = None,
		client_order_id: Optional[str] = None,
	) -> OrderResult:
		"""Cancel an existing order.

		Args:
		    symbol: Trading pair symbol
		    order_id: Exchange order ID
		    client_order_id: Client order ID

		Returns:
		    Cancel result
		"""
		try:
			response = await self.client.cancel_order(
				symbol=symbol,
				order_id=int(order_id) if order_id else None,
				orig_client_order_id=client_order_id,
			)

			# Remove from active orders
			if order_id and order_id in self._active_orders:
				del self._active_orders[order_id]

			result = OrderResult(
				success=True,
				order_id=str(response.get('orderId')),
				client_order_id=response.get('clientOrderId'),
				status=OrderStatus.CANCELED,
				raw_response=response,
			)

			logger.info(f'Order canceled: {order_id or client_order_id}')
			return result

		except Exception as e:
			logger.error(f'Failed to cancel order: {e}')
			return OrderResult(success=False, error_message=str(e))

	async def get_order_status(
		self,
		symbol: str,
		order_id: Optional[str] = None,
		client_order_id: Optional[str] = None,
	) -> OrderResult:
		"""Get order status.

		Args:
		    symbol: Trading pair symbol
		    order_id: Exchange order ID
		    client_order_id: Client order ID

		Returns:
		    Order status result
		"""
		try:
			response = await self.client.get_order(
				symbol=symbol,
				order_id=int(order_id) if order_id else None,
				orig_client_order_id=client_order_id,
			)

			result = OrderResult(
				success=True,
				order_id=str(response.get('orderId')),
				client_order_id=response.get('clientOrderId'),
				status=OrderStatus(response.get('status')),
				filled_quantity=float(response.get('executedQty', 0)),
				filled_price=float(response.get('price', 0))
				if response.get('price')
				else 0,
				raw_response=response,
			)

			return result

		except Exception as e:
			logger.error(f'Failed to get order status: {e}')
			return OrderResult(success=False, error_message=str(e))

	# Convenience methods for crypto_agents integration

	async def buy_market(
		self, symbol: str, quantity: float, client_order_id: Optional[str] = None
	) -> OrderResult:
		"""Place market buy order.

		Args:
		    symbol: Trading pair symbol
		    quantity: Quantity to buy
		    client_order_id: Optional client order ID

		Returns:
		    Order result
		"""
		request = OrderRequest(
			symbol=symbol,
			side=OrderSide.BUY,
			order_type=OrderType.MARKET,
			quantity=quantity,
			client_order_id=client_order_id,
		)

		return await self.place_order(request)

	async def sell_market(
		self, symbol: str, quantity: float, client_order_id: Optional[str] = None
	) -> OrderResult:
		"""Place market sell order.

		Args:
		    symbol: Trading pair symbol
		    quantity: Quantity to sell
		    client_order_id: Optional client order ID

		Returns:
		    Order result
		"""
		request = OrderRequest(
			symbol=symbol,
			side=OrderSide.SELL,
			order_type=OrderType.MARKET,
			quantity=quantity,
			client_order_id=client_order_id,
		)

		return await self.place_order(request)

	async def buy_limit(
		self,
		symbol: str,
		quantity: float,
		price: float,
		client_order_id: Optional[str] = None,
	) -> OrderResult:
		"""Place limit buy order.

		Args:
		    symbol: Trading pair symbol
		    quantity: Quantity to buy
		    price: Limit price
		    client_order_id: Optional client order ID

		Returns:
		    Order result
		"""
		request = OrderRequest(
			symbol=symbol,
			side=OrderSide.BUY,
			order_type=OrderType.LIMIT,
			quantity=quantity,
			price=price,
			client_order_id=client_order_id,
		)

		return await self.place_order(request)

	async def sell_limit(
		self,
		symbol: str,
		quantity: float,
		price: float,
		client_order_id: Optional[str] = None,
	) -> OrderResult:
		"""Place limit sell order.

		Args:
		    symbol: Trading pair symbol
		    quantity: Quantity to sell
		    price: Limit price
		    client_order_id: Optional client order ID

		Returns:
		    Order result
		"""
		request = OrderRequest(
			symbol=symbol,
			side=OrderSide.SELL,
			order_type=OrderType.LIMIT,
			quantity=quantity,
			price=price,
			client_order_id=client_order_id,
		)

		return await self.place_order(request)

	def get_trading_stats(self) -> Dict[str, Any]:
		"""Get trading statistics.

		Returns:
		    Trading statistics
		"""
		successful_orders = [order for order in self._order_history if order.success]
		filled_orders = [
			order for order in successful_orders if order.filled_quantity > 0
		]

		total_volume = sum(
			order.filled_quantity * order.filled_price for order in filled_orders
		)

		return {
			'total_orders': len(self._order_history),
			'successful_orders': len(successful_orders),
			'filled_orders': len(filled_orders),
			'active_orders': len(self._active_orders),
			'total_volume_usd': total_volume,
			'daily_volume_usd': self.risk_limits.daily_volume_usd,
			'risk_limits': {
				'max_position_size_usd': self.risk_limits.max_position_size_usd,
				'max_order_size_usd': self.risk_limits.max_order_size_usd,
				'max_daily_volume_usd': self.risk_limits.max_daily_volume_usd,
				'daily_volume_remaining': self.risk_limits.max_daily_volume_usd
				- self.risk_limits.daily_volume_usd,
			},
		}

