#!/usr/bin/env python3
"""
Setup script for Binance Wallet Integration

This script helps set up the Binance integration for the crypto_agents system.
"""

import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_python_version():
	"""Check if Python version is compatible."""
	if sys.version_info < (3, 8):
		logger.error('Python 3.8 or higher is required')
		return False

	logger.info(f'Python version: {sys.version}')
	return True


def install_dependencies():
	"""Install required dependencies using Poetry."""
	logger.info('Installing dependencies with Poetry...')

	# Check if we're in a Poetry environment
	try:
		# First try using Poetry to add dependencies
		subprocess.check_call(
			['poetry', '--version'],
			stdout=subprocess.DEVNULL,
			stderr=subprocess.DEVNULL,
		)

		# Add the required dependencies to the Poetry project
		dependencies = [
			'aiohttp>=3.8.0',
			'websockets>=11.0.0',
			'pytest>=7.0.0',
			'pytest-asyncio>=0.21.0',
		]

		for dep in dependencies:
			try:
				subprocess.check_call(['poetry', 'add', dep])
				logger.info(f'Added {dep} to Poetry project')
			except subprocess.CalledProcessError:
				logger.warning(f'Failed to add {dep}, it might already exist')

		# Install the project dependencies
		subprocess.check_call(['poetry', 'install'])
		logger.info('Dependencies installed successfully with Poetry')
		return True

	except (subprocess.CalledProcessError, FileNotFoundError):
		logger.warning('Poetry not found, falling back to pip installation')

		# Fallback to pip installation
		requirements_file = Path(__file__).parent / 'requirements.txt'

		try:
			subprocess.check_call(
				[sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)]
			)
			logger.info('Dependencies installed successfully with pip')
			return True
		except subprocess.CalledProcessError as e:
			logger.error(f'Failed to install dependencies: {e}')
			return False


def run_tests():
	"""Run integration tests using Poetry if available."""
	logger.info('Running tests...')

	test_file = Path(__file__).parent / 'tests' / 'test_integration.py'

	try:
		# Try running tests with Poetry first
		try:
			subprocess.check_call(
				['poetry', '--version'],
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL,
			)
			# Run basic tests (not requiring API keys) with Poetry
			subprocess.check_call(
				[
					'poetry',
					'run',
					'pytest',
					str(test_file),
					'-v',
					'-k',
					'not integration',
				]
			)
			logger.info('Basic tests passed with Poetry')
			return True
		except (subprocess.CalledProcessError, FileNotFoundError):
			# Fallback to direct pytest execution
			subprocess.check_call(
				[
					sys.executable,
					'-m',
					'pytest',
					str(test_file),
					'-v',
					'-k',
					'not integration',
				]
			)
			logger.info('Basic tests passed with direct pytest')
			return True
	except subprocess.CalledProcessError as e:
		logger.warning(f'Some tests failed: {e}')
		return False


def validate_setup():
	"""Validate that the integration is working."""
	logger.info('Validating setup...')

	try:
		# Try importing the main components
		from binance_wallet_integration import (
			BinanceClient,
			ConfigManager,
			OrderManager,
			WebSocketManager,
		)

		# Test configuration
		config = ConfigManager()
		logger.info(f'Configuration loaded for environment: {config.environment.value}')

		# Test that we can create clients (without API calls)
		client = BinanceClient(config)
		logger.info('BinanceClient initialized successfully')

		logger.info('✅ Integration setup validation passed!')
		return True

	except ImportError as e:
		logger.error(f'Import error: {e}')
		return False
	except Exception as e:
		logger.error(f'Validation error: {e}')
		return False


def print_next_steps():
	"""Print next steps for the user."""
	print('\n' + '=' * 60)
	print('🎉 BINANCE INTEGRATION SETUP COMPLETE!')
	print('=' * 60)
	print()
	print('📋 NEXT STEPS:')
	print()
	print('1. 🔐 Set up API keys:')
	print('   - Get testnet keys: https://testnet.binance.vision/')
	print('   - Edit .env file with your API keys')
	print()
	print('2. 🧪 Test the integration:')
	print('   poetry run python binance_wallet_integration/examples/basic_usage.py')
	print(
		'   # Or without Poetry: python binance_wallet_integration/examples/basic_usage.py'
	)
	print()
	print('3. 🔄 Integrate with crypto_agents:')
	print('   - Replace buy/sell functions in portfolio_manager.py')
	print('   - Use CryptoAgentsAdapter for seamless integration')
	print()
	print('4. 📚 Read the documentation:')
	print('   cat binance_wallet_integration/README.md')
	print()
	print('⚠️  SAFETY REMINDERS:')
	print('- Always start with testnet environment')
	print('- Use small amounts for initial testing')
	print('- Set conservative risk limits')
	print('- Monitor automated trading closely')
	print()
	print('🚀 Happy trading!')
	print('=' * 60)


def main():
	"""Main setup function."""
	print('🔧 Setting up Binance Wallet Integration...')
	print()

	# Check prerequisites
	if not check_python_version():
		sys.exit(1)

	# Install dependencies
	if not install_dependencies():
		logger.error('Failed to install dependencies')
		sys.exit(1)

	# Run tests
	if not run_tests():
		logger.warning('Some tests failed, but continuing...')

	# Validate setup
	if not validate_setup():
		logger.error('Setup validation failed')
		sys.exit(1)

	# Print next steps
	print_next_steps()


if __name__ == '__main__':
	main()
