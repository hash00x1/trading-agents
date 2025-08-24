#!/usr/bin/env python3
"""
Wallet Testing Script for Binance Integration

This script tests the Binance wallet integration by:
1. Checking account balances
2. Placing a small BTC test order
3. Verifying order execution

Supports both HMAC-SHA256 and Ed25519 authentication methods.
"""

import asyncio
import os
import sys
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add the parent directory to the path to import binance_wallet_integration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from binance_wallet_integration import (
	BinanceClient,
	ConfigManager,
	OrderManager,
	Environment,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
	level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WalletTester:
	"""Comprehensive wallet testing class for Binance integration."""

	def __init__(self, environment: Environment = Environment.TESTNET):
		"""Initialize the wallet tester.

		Args:
		    environment: Trading environment (TESTNET, MAINNET, or PAPER)
		"""
		self.environment = environment
		self.config = ConfigManager(environment)
		self.client = None
		self.order_manager = None

	async def initialize(self):
		"""Initialize the client and order manager."""
		try:
			self.client = BinanceClient(self.config)
			self.order_manager = OrderManager(self.client, self.config)
			await self.order_manager.initialize()
			logger.info(
				f'Initialized wallet tester for {self.environment.value} environment'
			)
		except Exception as e:
			logger.error(f'Failed to initialize wallet tester: {e}')
			raise

	async def check_authentication(self) -> Dict[str, Any]:
		"""Test authentication and basic connectivity.

		Returns:
		    Dict containing authentication test results
		"""
		logger.info('Testing authentication and connectivity...')

		try:
			# Test server time (public endpoint)
			server_time = await self.client.get_server_time()
			logger.info(f'Server time: {server_time}')

			# Test authenticated endpoint
			account_info = await self.client.get_account_info()

			return {
				'success': True,
				'server_time': server_time,
				'account_type': account_info.get('accountType', 'unknown'),
				'can_trade': account_info.get('canTrade', False),
				'can_withdraw': account_info.get('canWithdraw', False),
				'can_deposit': account_info.get('canDeposit', False),
				'permissions': account_info.get('permissions', []),
			}

		except Exception as e:
			logger.error(f'Authentication test failed: {e}')
			return {'success': False, 'error': str(e)}

	async def get_wallet_balances(self) -> Dict[str, Any]:
		"""Get and display wallet balances.

		Returns:
		    Dict containing balance information
		"""
		logger.info('Fetching wallet balances...')

		try:
			account_info = await self.client.get_account_info()
			balances = account_info.get('balances', [])

			# Filter out zero balances and format for display
			non_zero_balances = []
			total_btc_value = Decimal('0')

			for balance in balances:
				free = Decimal(balance['free'])
				locked = Decimal(balance['locked'])
				total = free + locked

				if total > 0:
					asset_info = {
						'asset': balance['asset'],
						'free': str(free),
						'locked': str(locked),
						'total': str(total),
					}
					non_zero_balances.append(asset_info)

					# Calculate approximate BTC value for major assets
					if balance['asset'] == 'BTC':
						total_btc_value += total
					elif balance['asset'] == 'USDT':
						# Rough conversion assuming 1 BTC = 50000 USDT
						btc_price = await self._get_btc_price_usdt()
						if btc_price:
							total_btc_value += total / Decimal(str(btc_price))

			logger.info(f'Found {len(non_zero_balances)} assets with balances')
			for balance in non_zero_balances:
				logger.info(
					f'  {balance["asset"]}: {balance["total"]} (Free: {balance["free"]}, Locked: {balance["locked"]})'
				)

			return {
				'success': True,
				'balances': non_zero_balances,
				'total_btc_value_estimate': str(total_btc_value),
				'balance_count': len(non_zero_balances),
			}

		except Exception as e:
			logger.error(f'Failed to fetch balances: {e}')
			return {'success': False, 'error': str(e)}

	async def _get_btc_price_usdt(self) -> Optional[float]:
		"""Get current BTC/USDT price."""
		try:
			ticker = await self.client.get_symbol_price('BTCUSDT')
			return float(ticker['price'])
		except Exception:
			return None

	async def check_trading_permissions(
		self, symbol: str = 'BTCUSDT'
	) -> Dict[str, Any]:
		"""Check trading permissions and symbol information.

		Args:
		    symbol: Trading pair to check

		Returns:
		    Dict containing trading permission information
		"""
		logger.info(f'Checking trading permissions for {symbol}...')

		try:
			# Get exchange info for the symbol
			exchange_info = await self.client.get_exchange_info()
			symbol_info = None

			for sym in exchange_info.get('symbols', []):
				if sym['symbol'] == symbol:
					symbol_info = sym
					break

			if not symbol_info:
				return {'success': False, 'error': f'Symbol {symbol} not found'}

			# Extract important trading information
			filters = {
				filter_info['filterType']: filter_info
				for filter_info in symbol_info.get('filters', [])
			}

			result = {
				'success': True,
				'symbol': symbol,
				'status': symbol_info.get('status'),
				'base_asset': symbol_info.get('baseAsset'),
				'quote_asset': symbol_info.get('quoteAsset'),
				'is_spot_trading_allowed': symbol_info.get(
					'isSpotTradingAllowed', False
				),
				'permissions': symbol_info.get('permissions', []),
				'filters': {},
			}

			# Add relevant filters
			if 'LOT_SIZE' in filters:
				result['filters']['lot_size'] = {
					'min_qty': filters['LOT_SIZE']['minQty'],
					'max_qty': filters['LOT_SIZE']['maxQty'],
					'step_size': filters['LOT_SIZE']['stepSize'],
				}

			if 'MIN_NOTIONAL' in filters:
				result['filters']['min_notional'] = filters['MIN_NOTIONAL'][
					'minNotional'
				]

			if 'PRICE_FILTER' in filters:
				result['filters']['price_filter'] = {
					'min_price': filters['PRICE_FILTER']['minPrice'],
					'max_price': filters['PRICE_FILTER']['maxPrice'],
					'tick_size': filters['PRICE_FILTER']['tickSize'],
				}

			logger.info(f'Symbol {symbol} status: {result["status"]}')
			logger.info(f'Spot trading allowed: {result["is_spot_trading_allowed"]}')

			return result

		except Exception as e:
			logger.error(f'Failed to check trading permissions: {e}')
			return {'success': False, 'error': str(e)}

	async def place_small_btc_order(
		self, order_type: str = 'test', quantity: float = 0.0001
	) -> Dict[str, Any]:
		"""Place a small BTC order for testing.

		Args:
		    order_type: 'test' for test order, 'real' for actual order
		    quantity: BTC quantity to trade (default: 0.0001 BTC ~= $5 at $50k)

		Returns:
		    Dict containing order result
		"""
		symbol = 'BTCUSDT'
		logger.info(f'Placing {order_type} order: BUY {quantity} {symbol}')

		try:
			# Get current price
			ticker = await self.client.get_symbol_price(symbol)
			current_price = float(ticker['price'])
			estimated_cost = quantity * current_price

			logger.info(f'Current BTC price: ${current_price:,.2f}')
			logger.info(f'Estimated order cost: ${estimated_cost:.2f}')

			# Check if we have sufficient balance
			balances = await self.get_wallet_balances()
			if not balances['success']:
				return {'success': False, 'error': 'Failed to check balances'}

			usdt_balance = None
			for balance in balances['balances']:
				if balance['asset'] == 'USDT':
					usdt_balance = float(balance['free'])
					break

			if usdt_balance is None:
				return {'success': False, 'error': 'No USDT balance found'}

			if usdt_balance < estimated_cost:
				return {
					'success': False,
					'error': f'Insufficient USDT balance. Need ${estimated_cost:.2f}, have ${usdt_balance:.2f}',
				}

			# Place the order
			if order_type == 'test':
				# Use test order endpoint
				result = await self.order_manager.buy_market(symbol, quantity)

				return {
					'success': result.success,
					'order_type': 'test',
					'symbol': symbol,
					'side': 'BUY',
					'quantity': quantity,
					'estimated_cost': estimated_cost,
					'current_price': current_price,
					'result': {
						'filled_quantity': result.filled_quantity,
						'filled_price': result.filled_price,
						'error_message': result.error_message
						if not result.success
						else None,
					},
				}
			else:
				# This would be for real orders - be very careful!
				logger.warning('Real order placement not implemented for safety')
				return {
					'success': False,
					'error': 'Real order placement disabled for safety',
				}

		except Exception as e:
			logger.error(f'Failed to place order: {e}')
			return {'success': False, 'error': str(e)}

	async def run_comprehensive_test(self) -> Dict[str, Any]:
		"""Run a comprehensive wallet test.

		Returns:
		    Dict containing all test results
		"""
		logger.info('=== Starting Comprehensive Wallet Test ===')

		results = {
			'environment': self.environment.value,
			'timestamp': asyncio.get_event_loop().time(),
			'tests': {},
		}

		# Test 1: Authentication
		auth_result = await self.check_authentication()
		results['tests']['authentication'] = auth_result

		if not auth_result['success']:
			logger.error('Authentication failed, stopping tests')
			return results

		# Test 2: Wallet Balances
		balance_result = await self.get_wallet_balances()
		results['tests']['balances'] = balance_result

		# Test 3: Trading Permissions
		permission_result = await self.check_trading_permissions()
		results['tests']['trading_permissions'] = permission_result

		# Test 4: Small BTC Order (test mode)
		if balance_result['success'] and permission_result['success']:
			order_result = await self.place_small_btc_order('test', 0.0001)
			results['tests']['test_order'] = order_result

		# Summary
		successful_tests = sum(
			1 for test in results['tests'].values() if test.get('success', False)
		)
		total_tests = len(results['tests'])

		results['summary'] = {
			'successful_tests': successful_tests,
			'total_tests': total_tests,
			'success_rate': f'{successful_tests / total_tests * 100:.1f}%',
		}

		logger.info(
			f'=== Test Summary: {successful_tests}/{total_tests} tests passed ==='
		)

		return results

	async def close(self):
		"""Clean up resources."""
		if self.client:
			await self.client.close()


async def main():
	"""Main function to run wallet tests."""

	# Check for required environment variables
	required_env_vars = ['BINANCE_API_KEY']
	auth_methods = []

	if os.getenv('BINANCE_API_SECRET'):
		auth_methods.append('HMAC-SHA256')
	if os.getenv('BINANCE_PRIVATE_KEY_PATH'):
		auth_methods.append('Ed25519')

	if not auth_methods:
		logger.error('No authentication method configured!')
		logger.error(
			'Set either BINANCE_API_SECRET or BINANCE_PRIVATE_KEY_PATH environment variable'
		)
		return

	logger.info(f'Using authentication method(s): {", ".join(auth_methods)}')

	# Determine environment
	env_str = os.getenv('BINANCE_ENVIRONMENT', 'testnet').lower()
	if env_str == 'mainnet':
		logger.warning('MAINNET environment detected!')
		logger.warning(
			'This will use real money. Are you sure? (Set BINANCE_ENVIRONMENT=testnet for testing)'
		)
		environment = Environment.MAINNET
	elif env_str == 'paper':
		environment = Environment.PAPER
	else:
		environment = Environment.TESTNET

	# Run tests
	tester = WalletTester(environment)

	try:
		await tester.initialize()
		results = await tester.run_comprehensive_test()

		# Print results
		print('\n' + '=' * 60)
		print('WALLET TEST RESULTS')
		print('=' * 60)
		print(f'Environment: {results["environment"]}')
		print(f'Success Rate: {results["summary"]["success_rate"]}')
		print()

		for test_name, test_result in results['tests'].items():
			status = '✅ PASS' if test_result.get('success', False) else '❌ FAIL'
			print(f'{test_name}: {status}')
			if not test_result.get('success', False) and 'error' in test_result:
				print(f'  Error: {test_result["error"]}')

		print('=' * 60)

		# Detailed balance information
		if 'balances' in results['tests'] and results['tests']['balances']['success']:
			balance_data = results['tests']['balances']
			print(f'\nWallet Balances ({balance_data["balance_count"]} assets):')
			for balance in balance_data['balances']:
				print(f'  {balance["asset"]}: {balance["total"]}')
			print(
				f'Estimated total value: {balance_data["total_btc_value_estimate"]} BTC'
			)

		# Order information
		if 'test_order' in results['tests']:
			order_data = results['tests']['test_order']
			print('\nTest Order Result:')
			if order_data['success']:
				print('  ✅ Successfully placed test order')
				print(f'  Quantity: {order_data["quantity"]} BTC')
				print(f'  Estimated cost: ${order_data["estimated_cost"]:.2f}')
			else:
				print(
					f'  ❌ Test order failed: {order_data.get("error", "Unknown error")}'
				)

	except Exception as e:
		logger.error(f'Test execution failed: {e}')
	finally:
		await tester.close()


if __name__ == '__main__':
	asyncio.run(main())
