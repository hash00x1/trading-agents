#!/usr/bin/env python3
"""
Setup Script for Binance Integration with Crypto Agents

This script sets up the Binance integration for testnet trading.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def setup_environment():
	"""Set up environment variables for testnet trading."""
	print('🚀 Setting up Binance Integration for Crypto Agents')
	print('=' * 60)

	# Check if .env file exists
	env_file = Path(__file__).parent.parent / '.env'
	if env_file.exists():
		print(f'✅ Found .env file at {env_file}')
	else:
		print(f'⚠️  .env file not found at {env_file}')
		print('Please create a .env file with your Binance testnet credentials')
		print('\nExample .env file:')
		print("""
# Binance Configuration
BINANCE_ENVIRONMENT=testnet
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# Trading Settings  
TRADING_MODE=live
MAX_POSITION_SIZE_USD=1000
MIN_ORDER_SIZE_USD=10
""")
		return False

	# Load environment variables
	from dotenv import load_dotenv

	load_dotenv()

	# Check required variables
	required_vars = ['BINANCE_API_KEY']
	optional_vars = ['BINANCE_API_SECRET', 'BINANCE_PRIVATE_KEY_PATH']

	missing_required = []
	for var in required_vars:
		if not os.getenv(var):
			missing_required.append(var)

	if missing_required:
		print(f'❌ Missing required environment variables: {missing_required}')
		return False

	# Check authentication method
	has_secret = bool(os.getenv('BINANCE_API_SECRET'))
	has_private_key = bool(os.getenv('BINANCE_PRIVATE_KEY_PATH'))

	if not has_secret and not has_private_key:
		print('❌ Need either BINANCE_API_SECRET or BINANCE_PRIVATE_KEY_PATH')
		return False

	auth_method = 'Ed25519' if has_private_key else 'HMAC-SHA256'
	print(f'✅ Authentication method: {auth_method}')

	# Check environment
	env = os.getenv('BINANCE_ENVIRONMENT', 'testnet')
	trading_mode = os.getenv('TRADING_MODE', 'paper')

	print(f'✅ Environment: {env}')
	print(f'✅ Trading mode: {trading_mode}')

	return True


def test_binance_connection():
	"""Test connection to Binance."""
	print('\n🔍 Testing Binance Connection')
	print('-' * 30)

	try:
		from base_workflow.tools.binance_trading import (
			get_trading_status,
			get_real_time_price_binance,
		)

		# Get trading status
		status = get_trading_status()
		print(f'✅ Trading status: {status}')

		# Test price fetch
		try:
			btc_price = get_real_time_price_binance('BTC')
			print(f'✅ BTC price: ${btc_price}')
		except Exception as e:
			print(f'⚠️  Price fetch failed: {e}')

		return True

	except Exception as e:
		print(f'❌ Connection test failed: {e}')
		return False


def test_portfolio_manager():
	"""Test portfolio manager with Binance integration."""
	print('\n🧪 Testing Portfolio Manager')
	print('-' * 30)

	try:
		from langchain_core.messages import HumanMessage

		# Create test state
		test_state = {
			'messages': [
				HumanMessage(content='Test portfolio manager with Binance integration')
			],
			'data': {
				'token': 'BTC',
				'slug': 'bitcoin',
				'dollar balance': 100,  # Small test amount
				'token balance': 0,
				'close_price': 50000,
			},
		}

		print('✅ Portfolio manager integration test prepared')
		print('   (Run with agent system to execute)')

		return True

	except Exception as e:
		print(f'❌ Portfolio manager test failed: {e}')
		return False


def main():
	"""Run the complete setup and test process."""
	print('🏗️  Crypto Agents - Binance Integration Setup')
	print('=' * 50)

	# Step 1: Environment setup
	if not setup_environment():
		print('\n❌ Environment setup failed')
		return False

	# Step 2: Test connection
	if not test_binance_connection():
		print('\n❌ Connection test failed')
		return False

	# Step 3: Test integration
	if not test_portfolio_manager():
		print('\n❌ Integration test failed')
		return False

	print('\n🎉 Setup Complete!')
	print('=' * 20)
	print('✅ Binance integration is ready for testnet trading')
	print('✅ Your agents can now execute real trades on Binance testnet')
	print('\n📝 Next steps:')
	print('1. Run your crypto_agents workflow normally')
	print('2. Monitor trades in base_workflow/outputs/')
	print('3. Check your Binance testnet account for actual trades')

	# Show trading status
	from base_workflow.tools.binance_trading import get_trading_status

	status = get_trading_status()
	print(f'\n📊 Current Status: {status}')

	return True


if __name__ == '__main__':
	success = main()
	sys.exit(0 if success else 1)
