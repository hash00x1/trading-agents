"""
Basic Usage Examples for Binance Wallet Integration

Demonstrates how to use the Binance integration with crypto_agents.
"""

import asyncio
import logging
import os
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our Binance integration
from binance_wallet_integration import (
	BinanceClient,
	ConfigManager,
	OrderManager,
	WebSocketManager,
	Environment,
)
from binance_wallet_integration.order_manager import OrderRequest, OrderSide, OrderType


async def basic_client_example():
	"""Basic REST API client usage."""
	print('\n=== Basic Binance Client Example ===')

	# Initialize with testnet environment
	config = ConfigManager(Environment.TESTNET)

	async with BinanceClient(config) as client:
		try:
			# Get exchange information
			exchange_info = await client.get_exchange_info()
			print(f'Connected to Binance {config.environment.value}')
			print(f'Server time: {exchange_info.get("serverTime")}')

			# Get current Bitcoin price
			btc_price = await client.get_symbol_price('BTCUSDT')
			print(f'Current BTC price: ${btc_price["price"]}')

			# Get BTC order book
			order_book = await client.get_order_book('BTCUSDT', limit=5)
			print(
				f'BTC order book - Best bid: {order_book["bids"][0][0]}, Best ask: {order_book["asks"][0][0]}'
			)

			# Get account info (if API keys are configured)
			try:
				account = await client.get_account_info()
				print(f'Account type: {account.get("accountType")}')

				# Show some balances
				balances = account.get('balances', [])
				non_zero_balances = [
					b
					for b in balances
					if float(b['free']) > 0 or float(b['locked']) > 0
				]
				print(f'Non-zero balances: {len(non_zero_balances)}')

			except Exception as e:
				print(f'Account info not available (check API keys): {e}')

		except Exception as e:
			logger.error(f'Error in basic client example: {e}')


async def order_management_example():
	"""Order management with risk controls."""
	print('\n=== Order Management Example ===')

	config = ConfigManager(Environment.TESTNET)

	async with BinanceClient(config) as client:
		try:
			# Initialize order manager
			order_manager = OrderManager(client, config)
			await order_manager.initialize()

			# Create a test buy order (small amount for testing)
			buy_request = OrderRequest(
				symbol='BTCUSDT',
				side=OrderSide.BUY,
				order_type=OrderType.LIMIT,
				quantity=0.001,  # Small amount for testing
				price=30000.0,  # Low price to avoid accidental execution
			)

			# Dry run first
			dry_result = await order_manager.place_order(buy_request, dry_run=True)
			print(
				f'Dry run result: {dry_result.success}, filled: {dry_result.filled_quantity}'
			)

			# Place test order (safe on testnet)
			if config.is_testnet() or config.is_paper_trading():
				real_result = await order_manager.place_order(buy_request)
				print(f'Test order result: {real_result.success}')
				if real_result.success:
					print(f'Order ID: {real_result.order_id}')

			# Get trading statistics
			stats = order_manager.get_trading_stats()
			print(f'Trading stats: {stats}')

		except Exception as e:
			logger.error(f'Error in order management example: {e}')


async def websocket_example():
	"""WebSocket real-time data streams."""
	print('\n=== WebSocket Streams Example ===')

	config = ConfigManager(Environment.TESTNET)
	ws_manager = WebSocketManager(config)

	# Message handlers
	async def handle_btc_trades(data: Dict[str, Any]):
		"""Handle BTC trade updates."""
		trade_data = data.get('data', {})
		price = trade_data.get('p', 'N/A')
		quantity = trade_data.get('q', 'N/A')
		print(f'BTC Trade: {quantity} @ ${price}')

	async def handle_btc_ticker(data: Dict[str, Any]):
		"""Handle BTC ticker updates."""
		ticker_data = data.get('data', {})
		price = ticker_data.get('c', 'N/A')  # Close price
		change = ticker_data.get('P', 'N/A')  # Percentage change
		print(f'BTC Ticker: ${price} ({change}%)')

	try:
		await ws_manager.start()

		# Subscribe to streams
		await ws_manager.subscribe_to_trades('BTCUSDT', handle_btc_trades)
		await ws_manager.subscribe_to_ticker('BTCUSDT', handle_btc_ticker)

		print('WebSocket streams active. Listening for 30 seconds...')
		await asyncio.sleep(30)  # Listen for 30 seconds

	except Exception as e:
		logger.error(f'Error in WebSocket example: {e}')

	finally:
		await ws_manager.stop()


async def integration_with_crypto_agents():
	"""Example integration with existing crypto_agents system."""
	print('\n=== Crypto Agents Integration Example ===')

	config = ConfigManager(Environment.TESTNET)

	async with BinanceClient(config) as client:
		try:
			order_manager = OrderManager(client, config)
			await order_manager.initialize()

			# Simulate crypto_agents decision
			agent_decision = {
				'symbol': 'BTCUSDT',
				'action': 'BUY',
				'quantity': 0.001,
				'confidence': 0.8,
				'reasoning': 'Technical analysis indicates bullish trend',
			}

			print(f'Agent decision: {agent_decision}')

			# Convert to order based on agent decision
			if agent_decision['action'] == 'BUY':
				# Get current price for market order
				price_data = await client.get_symbol_price(agent_decision['symbol'])
				current_price = float(price_data['price'])

				# Place market buy order
				result = await order_manager.buy_market(
					symbol=agent_decision['symbol'], quantity=agent_decision['quantity']
				)

				print(f'Order execution result: {result.success}')
				if result.success:
					print(f'Filled: {result.filled_quantity} @ ${result.filled_price}')

					# This would update the crypto_agents database
					print(
						'Would update crypto_agents SQLite database with trade result'
					)

		except Exception as e:
			logger.error(f'Error in integration example: {e}')


async def main():
	"""Run all examples."""
	print('Binance Wallet Integration Examples')
	print('=' * 50)

	# Check environment variables
	if not os.getenv('BINANCE_API_KEY'):
		print('⚠️  BINANCE_API_KEY not set - some examples will use mock data')

	if not os.getenv('BINANCE_API_SECRET'):
		print('⚠️  BINANCE_API_SECRET not set - some examples will use mock data')

	print(f'Environment: {os.getenv("BINANCE_ENVIRONMENT", "testnet")}')
	print()

	try:
		# Run examples
		await basic_client_example()
		await order_management_example()
		await websocket_example()
		await integration_with_crypto_agents()

		print('\n✅ All examples completed successfully!')

	except KeyboardInterrupt:
		print('\n⚠️  Examples interrupted by user')
	except Exception as e:
		logger.error(f'Error running examples: {e}')


if __name__ == '__main__':
	# Set environment to testnet for safety
	os.environ.setdefault('BINANCE_ENVIRONMENT', 'testnet')

	# Run examples
	asyncio.run(main())
