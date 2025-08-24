"""
Binance Integration Configuration for Crypto Agents

This module handles configuration for integrating Binance trading
capabilities into the crypto_agents base_workflow.
"""

import os
from binance_wallet_integration import Environment


class BinanceIntegrationConfig:
	"""Configuration for Binance integration with crypto_agents."""

	def __init__(self):
		# Environment detection
		env_str = os.getenv('BINANCE_ENVIRONMENT', 'testnet').lower()
		if env_str == 'mainnet':
			self.environment = Environment.MAINNET
		elif env_str == 'paper':
			self.environment = Environment.PAPER
		else:
			self.environment = Environment.TESTNET

		# Trading mode
		self.trading_mode = os.getenv(
			'TRADING_MODE', 'paper'
		).lower()  # 'paper' or 'live'

		# Risk management
		self.max_position_size_usd = float(os.getenv('MAX_POSITION_SIZE_USD', '1000'))
		self.min_order_size_usd = float(os.getenv('MIN_ORDER_SIZE_USD', '10'))

		# API credentials (will be read by binance_wallet_integration)
		self.api_key = os.getenv('BINANCE_API_KEY')
		self.api_secret = os.getenv('BINANCE_API_SECRET')
		self.private_key_path = os.getenv('BINANCE_PRIVATE_KEY_PATH')

	def is_live_trading_enabled(self) -> bool:
		"""Check if live trading is enabled."""
		return (
			self.trading_mode == 'live'
			and self.environment in [Environment.TESTNET, Environment.MAINNET]
			and (self.api_key is not None)
		)

	def validate_config(self) -> bool:
		"""Validate the configuration."""
		if not self.is_live_trading_enabled():
			return True  # Paper trading doesn't need validation

		# Check API credentials
		if not self.api_key:
			raise ValueError('BINANCE_API_KEY is required for live trading')

		if not self.api_secret and not self.private_key_path:
			raise ValueError(
				'Either BINANCE_API_SECRET or BINANCE_PRIVATE_KEY_PATH is required'
			)

		return True

	def get_environment_name(self) -> str:
		"""Get human-readable environment name."""
		return f'{self.environment.value} ({"live" if self.is_live_trading_enabled() else "paper"})'


# Global configuration instance
binance_config = BinanceIntegrationConfig()
