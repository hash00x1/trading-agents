"""
Integration Tests for Binance Wallet Integration

Comprehensive tests for the Binance integration system.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock

from binance_wallet_integration import (
	BinanceClient,
	ConfigManager,
	OrderManager,
	WebSocketManager,
	SecurityManager,
	Environment,
)
from binance_wallet_integration.order_manager import OrderRequest, OrderSide, OrderType
from binance_wallet_integration.rate_limiter import RateLimitManager, RateLimitType


class TestConfigManager:
	"""Test configuration management."""

	def test_environment_detection(self):
		"""Test environment detection from env vars."""
		with patch.dict(os.environ, {'BINANCE_ENVIRONMENT': 'testnet'}):
			config = ConfigManager()
			assert config.environment == Environment.TESTNET

		with patch.dict(os.environ, {'BINANCE_ENVIRONMENT': 'mainnet'}):
			config = ConfigManager()
			assert config.environment == Environment.MAINNET

	def test_config_validation(self):
		"""Test configuration validation."""
		config = ConfigManager(Environment.TESTNET)
		assert config.validate_config() == True

	def test_paper_trading_detection(self):
		"""Test paper trading mode detection."""
		config = ConfigManager(Environment.PAPER)
		assert config.is_paper_trading() == True

		config = ConfigManager(Environment.TESTNET)
		assert config.is_paper_trading() == False

	def test_api_credentials_paper_mode(self):
		"""Test API credentials in paper mode."""
		config = ConfigManager(Environment.PAPER)
		creds = config.get_api_credentials()
		assert creds['api_key'] == 'paper_key'
		assert creds['api_secret'] == 'paper_secret'


class TestSecurityManager:
	"""Test security and signing functionality."""

	def test_api_key_validation(self):
		"""Test API key validation."""
		# Valid key
		security = SecurityManager(
			'valid_api_key_with_sufficient_length',
			'valid_secret_key_with_sufficient_length',
		)
		assert security.api_key == 'valid_api_key_with_sufficient_length'

		# Invalid key
		with pytest.raises(ValueError):
			SecurityManager('', 'valid_secret')

		with pytest.raises(ValueError):
			SecurityManager('short', 'valid_secret')

	def test_signature_generation(self):
		"""Test HMAC signature generation."""
		security = SecurityManager('test_key', 'test_secret')

		params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET'}
		signature = security.generate_signature(params)

		assert isinstance(signature, str)
		assert len(signature) == 64  # SHA256 hex digest length

	def test_order_validation(self):
		"""Test order data validation."""
		security = SecurityManager('test_key', 'test_secret')

		# Valid order
		valid_order = {
			'symbol': 'BTCUSDT',
			'side': 'BUY',
			'type': 'MARKET',
			'quantity': '0.001',
		}
		assert security.validate_order_data(valid_order) == True

		# Invalid order - missing required field
		invalid_order = {'symbol': 'BTCUSDT', 'side': 'BUY'}
		with pytest.raises(ValueError):
			security.validate_order_data(invalid_order)

	def test_client_order_id_generation(self):
		"""Test client order ID generation."""
		order_id = SecurityManager.generate_client_order_id()
		assert order_id.startswith('crypto_agents_')
		assert len(order_id) > 20  # Should include timestamp and random suffix


class TestRateLimitManager:
	"""Test rate limiting functionality."""

	def test_rate_limit_initialization(self):
		"""Test rate limiter initialization."""
		rate_limiter = RateLimitManager()
		status = rate_limiter.get_status()

		assert status[RateLimitType.REQUEST_WEIGHT.value]['limit'] == 1200
		assert status[RateLimitType.ORDERS.value]['limit'] == 50

	def test_rate_limit_acquisition(self):
		"""Test rate limit acquisition."""
		rate_limiter = RateLimitManager()

		# Should be able to acquire initially
		assert rate_limiter.acquire(10, RateLimitType.REQUEST_WEIGHT, timeout=1) == True

		# Check usage updated
		status = rate_limiter.get_status()
		assert status[RateLimitType.REQUEST_WEIGHT.value]['current_usage'] == 10

	def test_rate_limit_exceeded(self):
		"""Test rate limit exceeded scenario."""
		rate_limiter = RateLimitManager()

		# Fill up the limit
		rate_limiter._rate_limits[RateLimitType.REQUEST_WEIGHT].current_usage = 1200

		# Should not be able to acquire
		assert rate_limiter.check_limits(1, RateLimitType.REQUEST_WEIGHT) == False

	def test_rate_limit_reset(self):
		"""Test rate limit reset functionality."""
		rate_limiter = RateLimitManager()

		# Add some usage
		rate_limiter.acquire(100, RateLimitType.REQUEST_WEIGHT, timeout=1)

		# Reset
		rate_limiter.reset_limits()

		# Should be back to zero
		status = rate_limiter.get_status()
		assert status[RateLimitType.REQUEST_WEIGHT.value]['current_usage'] == 0


class TestBinanceClient:
	"""Test Binance REST API client."""

	@pytest.fixture
	def mock_config(self):
		"""Mock configuration for testing."""
		config = Mock(spec=ConfigManager)
		config.environment = Environment.TESTNET
		config.endpoints = Mock()
		config.endpoints.rest_base = 'https://testnet.binance.vision'
		config.is_paper_trading.return_value = True
		config.get_api_credentials.return_value = {
			'api_key': 'test_key',
			'api_secret': 'test_secret',
		}
		config.validate_config.return_value = True
		return config

	@pytest.fixture
	def client(self, mock_config):
		"""Create client for testing."""
		return BinanceClient(mock_config)

	def test_client_initialization(self, client):
		"""Test client initialization."""
		assert client.config is not None
		assert client.security is not None
		assert client.rate_limiter is not None

	def test_endpoint_weight_calculation(self, client):
		"""Test API endpoint weight calculation."""
		# Test default weight
		weight = client._get_endpoint_weight('/api/v3/ticker/price')
		assert weight == 1

		# Test depth endpoint with different limits
		weight = client._get_endpoint_weight('/api/v3/depth', {'limit': 100})
		assert weight == 5

		weight = client._get_endpoint_weight('/api/v3/depth', {'limit': 500})
		assert weight == 25

	@patch('aiohttp.ClientSession.request')
	async def test_successful_request(self, mock_request, client):
		"""Test successful API request."""
		# Mock successful response
		mock_response = AsyncMock()
		mock_response.status = 200
		mock_response.text = AsyncMock(
			return_value='{"symbol": "BTCUSDT", "price": "50000.00"}'
		)
		mock_response.headers = {}
		mock_request.return_value.__aenter__.return_value = mock_response

		await client._ensure_session()
		result = await client._request(
			'GET', '/api/v3/ticker/price', {'symbol': 'BTCUSDT'}
		)

		assert result['symbol'] == 'BTCUSDT'
		assert result['price'] == '50000.00'

	@patch('aiohttp.ClientSession.request')
	async def test_rate_limit_error_handling(self, mock_request, client):
		"""Test rate limit error handling."""
		# Mock rate limit response
		mock_response = AsyncMock()
		mock_response.status = 429
		mock_response.text = AsyncMock(
			return_value='{"code": -1003, "msg": "Too many requests"}'
		)
		mock_response.headers = {'retry-after': '60'}
		mock_request.return_value.__aenter__.return_value = mock_response

		await client._ensure_session()

		with pytest.raises(Exception):  # Should raise BinanceAPIError
			await client._request('GET', '/api/v3/ticker/price')


class TestOrderManager:
	"""Test order management functionality."""

	@pytest.fixture
	def mock_client(self):
		"""Mock Binance client for testing."""
		client = AsyncMock(spec=BinanceClient)
		client.get_exchange_info.return_value = {
			'symbols': [
				{
					'symbol': 'BTCUSDT',
					'status': 'TRADING',
					'filters': [
						{
							'filterType': 'LOT_SIZE',
							'minQty': '0.00001',
							'maxQty': '9000',
							'stepSize': '0.00001',
						},
						{
							'filterType': 'PRICE_FILTER',
							'minPrice': '0.01',
							'maxPrice': '1000000',
							'tickSize': '0.01',
						},
						{'filterType': 'MIN_NOTIONAL', 'minNotional': '10.00'},
					],
				}
			]
		}
		client.get_symbol_price.return_value = {
			'symbol': 'BTCUSDT',
			'price': '50000.00',
		}
		return client

	@pytest.fixture
	def mock_config(self):
		"""Mock configuration for testing."""
		config = Mock(spec=ConfigManager)
		config.trading_config = Mock()
		config.trading_config.max_position_size_usd = 10000.0
		config.trading_config.min_order_size_usd = 10.0
		config.trading_config.slippage_tolerance = 0.005
		config.is_paper_trading.return_value = True
		return config

	@pytest.fixture
	async def order_manager(self, mock_client, mock_config):
		"""Create order manager for testing."""
		manager = OrderManager(mock_client, mock_config)
		await manager.initialize()
		return manager

	def test_quantity_formatting(self, order_manager):
		"""Test quantity formatting according to lot size."""
		formatted = order_manager._format_quantity('BTCUSDT', 0.123456789)
		assert formatted == '0.12345'  # Should round down to step size

	def test_price_formatting(self, order_manager):
		"""Test price formatting according to tick size."""
		formatted = order_manager._format_price('BTCUSDT', 50000.567)
		assert formatted == '50000.57'  # Should round to tick size

	async def test_order_validation(self, order_manager):
		"""Test order request validation."""
		# Valid order
		valid_request = OrderRequest(
			symbol='BTCUSDT',
			side=OrderSide.BUY,
			order_type=OrderType.MARKET,
			quantity=0.001,
		)
		order_manager._validate_order_request(valid_request)  # Should not raise

		# Invalid order - zero quantity
		invalid_request = OrderRequest(
			symbol='BTCUSDT',
			side=OrderSide.BUY,
			order_type=OrderType.MARKET,
			quantity=0,
		)
		with pytest.raises(ValueError):
			order_manager._validate_order_request(invalid_request)

	async def test_risk_limit_checks(self, order_manager):
		"""Test risk management limit checks."""
		# Valid order within limits
		valid_request = OrderRequest(
			symbol='BTCUSDT',
			side=OrderSide.BUY,
			order_type=OrderType.MARKET,
			quantity=0.001,  # ~$50 at $50k BTC
		)
		await order_manager._check_risk_limits(valid_request)  # Should not raise

		# Order too large
		large_request = OrderRequest(
			symbol='BTCUSDT',
			side=OrderSide.BUY,
			order_type=OrderType.MARKET,
			quantity=1.0,  # ~$50k at $50k BTC
		)
		with pytest.raises(ValueError):
			await order_manager._check_risk_limits(large_request)

	async def test_market_buy_order(self, order_manager, mock_client):
		"""Test market buy order placement."""
		mock_client.place_test_order.return_value = {}

		result = await order_manager.buy_market('BTCUSDT', 0.001)

		assert result.success == True
		assert result.filled_quantity == 0.001
		mock_client.place_test_order.assert_called_once()

	async def test_limit_sell_order(self, order_manager, mock_client):
		"""Test limit sell order placement."""
		mock_client.place_test_order.return_value = {}

		result = await order_manager.sell_limit('BTCUSDT', 0.001, 51000.0)

		assert result.success == True
		assert result.filled_quantity == 0.001
		assert result.filled_price == 51000.0
		mock_client.place_test_order.assert_called_once()


class TestWebSocketManager:
	"""Test WebSocket functionality."""

	@pytest.fixture
	def mock_config(self):
		"""Mock configuration for testing."""
		config = Mock(spec=ConfigManager)
		config.endpoints = Mock()
		config.endpoints.websocket_stream = 'wss://testnet.binance.vision/ws'
		return config

	@pytest.fixture
	def ws_manager(self, mock_config):
		"""Create WebSocket manager for testing."""
		return WebSocketManager(mock_config)

	def test_stream_name_formatting(self, ws_manager):
		"""Test stream name formatting."""
		from binance_wallet_integration.websocket_manager import (
			StreamConfig,
			StreamType,
		)

		# Trade stream
		config = StreamConfig(symbol='BTCUSDT', stream_type=StreamType.TRADE)
		stream_name = ws_manager._format_stream_name(config)
		assert stream_name == 'btcusdt@trade'

		# Kline stream
		config = StreamConfig(
			symbol='BTCUSDT', stream_type=StreamType.KLINE, interval='1m'
		)
		stream_name = ws_manager._format_stream_name(config)
		assert stream_name == 'btcusdt@kline_1m'

		# Depth stream
		config = StreamConfig(
			symbol='BTCUSDT', stream_type=StreamType.DEPTH, depth_levels=20
		)
		stream_name = ws_manager._format_stream_name(config)
		assert stream_name == 'btcusdt@depth20@100ms'

	def test_connection_rate_limiting(self, ws_manager):
		"""Test WebSocket connection rate limiting."""
		# Should be able to connect initially
		assert ws_manager._check_connection_rate_limit() == True

		# Simulate many connection attempts
		for _ in range(300):
			ws_manager._record_connection_attempt()

		# Should be rate limited now
		assert ws_manager._check_connection_rate_limit() == False

	async def test_message_handling(self, ws_manager):
		"""Test WebSocket message handling."""
		message_received = []

		async def test_handler(data):
			message_received.append(data)

		# Register handler
		ws_manager.register_handler('btcusdt@trade', test_handler)

		# Simulate incoming message
		test_message = (
			'{"stream": "btcusdt@trade", "data": {"p": "50000", "q": "0.001"}}'
		)
		await ws_manager._handle_message('test_conn', test_message)

		# Check handler was called
		assert len(message_received) == 1
		assert message_received[0]['stream'] == 'btcusdt@trade'


@pytest.mark.integration
class TestFullIntegration:
	"""Integration tests that test the full system."""

	@pytest.mark.asyncio
	async def test_end_to_end_testnet_connection(self):
		"""Test end-to-end connection to Binance testnet."""
		# Skip if no API keys
		if not os.getenv('BINANCE_API_KEY') or not os.getenv('BINANCE_API_SECRET'):
			pytest.skip('API keys not configured')

		config = ConfigManager(Environment.TESTNET)

		async with BinanceClient(config) as client:
			# Test basic connectivity
			exchange_info = await client.get_exchange_info()
			assert 'serverTime' in exchange_info

			# Test market data
			btc_price = await client.get_symbol_price('BTCUSDT')
			assert 'price' in btc_price
			assert float(btc_price['price']) > 0

	@pytest.mark.asyncio
	async def test_paper_trading_flow(self):
		"""Test complete paper trading flow."""
		config = ConfigManager(Environment.PAPER)

		async with BinanceClient(config) as client:
			order_manager = OrderManager(client, config)
			await order_manager.initialize()

			# Place test order
			result = await order_manager.buy_market('BTCUSDT', 0.001)

			assert result.success == True
			assert result.filled_quantity == 0.001

			# Check stats
			stats = order_manager.get_trading_stats()
			assert stats['total_orders'] == 1
			assert stats['successful_orders'] == 1


if __name__ == '__main__':
	# Run tests
	pytest.main([__file__, '-v'])
