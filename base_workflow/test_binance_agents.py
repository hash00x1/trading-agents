#!/usr/bin/env python3
"""
Test Script for Binance-Integrated Crypto Agents

This script demonstrates how the crypto agents now work with
real Binance testnet trading capabilities.
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

from langchain_core.messages import HumanMessage
from base_workflow.agents.portfolio_manager import portfolio_manager
from base_workflow.tools.binance_trading import get_trading_status, get_account_balances


def test_trading_status():
	"""Test and display current trading status."""
	print('📊 Current Trading Status')
	print('-' * 25)

	try:
		status = get_trading_status()
		for key, value in status.items():
			print(f'  {key}: {value}')
		return True
	except Exception as e:
		print(f'❌ Failed to get trading status: {e}')
		return False


def test_account_balances():
	"""Test and display account balances."""
	print('\n💰 Account Balances')
	print('-' * 18)

	try:
		balances = get_account_balances()
		if isinstance(balances, dict) and 'error' not in balances:
			if balances:
				for asset, balance in balances.items():
					if isinstance(balance, dict):
						print(
							f'  {asset}: {balance["total"]:.6f} (free: {balance["free"]:.6f})'
						)
					else:
						print(f'  {asset}: {balance}')
			else:
				print('  No balances found (or paper trading mode)')
		else:
			print(f'  {balances}')
		return True
	except Exception as e:
		print(f'❌ Failed to get balances: {e}')
		return False


def test_portfolio_manager_integration():
	"""Test portfolio manager with Binance integration."""
	print('\n🤖 Testing Portfolio Manager Integration')
	print('-' * 38)

	try:
		# Create a realistic test scenario
		simulated_analyst_signals = {
			'bitcoin': {
				'technical_analyst': {
					'signal': 'buy',
					'confidence': 0.8,
					'report': 'RSI showing oversold conditions, MACD bullish crossover detected.',
				},
				'sentiment_analyst': {
					'signal': 'buy',
					'confidence': 0.7,
					'report': 'Social sentiment improving, fear index dropping.',
				},
				'risk_manager': {
					'signal': 'hold',
					'confidence': 0.6,
					'report': 'Moderate volatility, position sizing recommended.',
				},
			}
		}

		# Create test state with small amounts for safety
		test_state = {
			'messages': [
				HumanMessage(content='Test trading decision based on analyst signals.'),
				HumanMessage(
					name='aggregated_analysts',
					content=json.dumps(simulated_analyst_signals),
				),
			],
			'data': {
				'token': 'BTC',
				'slug': 'bitcoin',
				'dollar balance': 50.0,  # Small test amount
				'token balance': 0.0,
				'close_price': 45000,
			},
			'metadata': {
				'request_id': 'test-binance-integration',
				'timestamp': '2025-01-27T12:00:00Z',
			},
		}

		print('📤 Sending test signals to portfolio manager...')
		print(f'   - Dollar balance: ${test_state["data"]["dollar balance"]}')
		print(f'   - Token: {test_state["data"]["token"]}')
		print(
			f'   - Simulated signals: {len(simulated_analyst_signals["bitcoin"])} analysts'
		)

		# Run portfolio manager
		result = portfolio_manager(test_state)

		print('📥 Portfolio manager response:')
		if 'messages' in result and result['messages']:
			last_message = result['messages'][-1]
			if hasattr(last_message, 'content'):
				try:
					analysis = json.loads(last_message.content)
					for slug, data in analysis.items():
						print(f'   - {slug}:')
						print(f'     Action: {data.get("action", "N/A")}')
						print(f'     Price: ${data.get("crypto_price", "N/A")}')
						print(f'     Decision: {data.get("decision", "N/A")[:100]}...')
				except json.JSONDecodeError:
					print(f'   Raw response: {last_message.content}')

		print('✅ Portfolio manager integration test completed')
		return True

	except Exception as e:
		print(f'❌ Portfolio manager test failed: {e}')
		import traceback

		print('Full error trace:')
		traceback.print_exc()
		return False


def main():
	"""Run comprehensive integration tests."""
	print('🧪 Crypto Agents - Binance Integration Test')
	print('=' * 45)

	# Test 1: Trading status
	status_ok = test_trading_status()

	# Test 2: Account balances
	balances_ok = test_account_balances()

	# Test 3: Portfolio manager integration
	portfolio_ok = test_portfolio_manager_integration()

	# Summary
	print('\n📋 Test Results Summary')
	print('-' * 22)
	print(f'  Trading Status: {"✅" if status_ok else "❌"}')
	print(f'  Account Balances: {"✅" if balances_ok else "❌"}')
	print(f'  Portfolio Manager: {"✅" if portfolio_ok else "❌"}')

	all_passed = status_ok and balances_ok and portfolio_ok

	if all_passed:
		print('\n🎉 All tests passed! Your agents are ready for testnet trading.')
		print('\n📝 What happens next:')
		print('   • Your agents will make real trading decisions')
		print('   • Orders will be sent to Binance testnet')
		print('   • Trades will be executed with real market prices')
		print('   • Results will be logged in base_workflow/outputs/')
	else:
		print('\n⚠️  Some tests failed. Please check your configuration.')
		print('   • Verify your .env file has correct testnet credentials')
		print('   • Ensure Binance testnet API is accessible')
		print('   • Check your API key permissions')

	return all_passed


if __name__ == '__main__':
	success = main()
	sys.exit(0 if success else 1)
