"""
Configuration Manager for Binance Integration

Handles environment variables, API endpoints, and trading parameters
with secure defaults and validation.
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
	"""Trading environment types."""

	TESTNET = 'testnet'
	MAINNET = 'mainnet'
	PAPER = 'paper'  # Simulation mode


@dataclass
class APIEndpoints:
	"""API endpoint configurations."""

	rest_base: str
	websocket_base: str
	websocket_stream: str


@dataclass
class RateLimits:
	"""Rate limiting configuration."""

	requests_per_minute: int = 1200
	orders_per_10_seconds: int = 50
	orders_per_24_hours: int = 160000
	websocket_connections_per_5_min: int = 300


@dataclass
class TradingConfig:
	"""Trading behavior configuration."""

	max_position_size_usd: float = 10000.0
	max_daily_loss_usd: float = 1000.0
	min_order_size_usd: float = 10.0
	slippage_tolerance: float = 0.005  # 0.5%
	order_timeout_seconds: int = 30


class ConfigManager:
	"""Manages configuration for Binance integration."""

	# API Endpoints by environment
	ENDPOINTS = {
		Environment.TESTNET: APIEndpoints(
			rest_base='https://testnet.binance.vision',
			websocket_base='wss://testnet.binance.vision',
			websocket_stream='wss://testnet.binance.vision/ws',
		),
		Environment.MAINNET: APIEndpoints(
			rest_base='https://api.binance.com',
			websocket_base='wss://stream.binance.com:9443',
			websocket_stream='wss://stream.binance.com:9443/ws',
		),
		Environment.PAPER: APIEndpoints(
			rest_base='https://testnet.binance.vision',  # Use testnet for paper trading
			websocket_base='wss://testnet.binance.vision',
			websocket_stream='wss://testnet.binance.vision/ws',
		),
	}

	def __init__(self, environment: Optional[Environment] = None):
		"""Initialize configuration manager.

		Args:
		    environment: Trading environment (defaults to TESTNET for safety)
		"""
		self.environment = environment or self._detect_environment()
		self.endpoints = self.ENDPOINTS[self.environment]
		self.rate_limits = RateLimits()
		self.trading_config = TradingConfig()

		# Load from environment variables
		self._load_from_env()

		logger.info(
			f'ConfigManager initialized for {self.environment.value} environment'
		)

	def _detect_environment(self) -> Environment:
		"""Auto-detect environment from environment variables."""
		env_str = os.getenv('BINANCE_ENVIRONMENT', 'testnet').lower()

		if env_str == 'mainnet':
			logger.warning(
				"MAINNET environment detected. Ensure you're ready for live trading!"
			)
			return Environment.MAINNET
		elif env_str == 'paper':
			return Environment.PAPER
		else:
			logger.info('Using TESTNET environment for safe development')
			return Environment.TESTNET

	def _load_from_env(self) -> None:
		"""Load configuration from environment variables."""
		# Rate limits (optional overrides)
		if requests_per_min := os.getenv('BINANCE_RATE_LIMIT_REQUESTS_PER_MIN'):
			self.rate_limits.requests_per_minute = int(requests_per_min)

		# Trading config overrides
		if max_position := os.getenv('BINANCE_MAX_POSITION_SIZE_USD'):
			self.trading_config.max_position_size_usd = float(max_position)

		if max_loss := os.getenv('BINANCE_MAX_DAILY_LOSS_USD'):
			self.trading_config.max_daily_loss_usd = float(max_loss)

		if min_order := os.getenv('BINANCE_MIN_ORDER_SIZE_USD'):
			self.trading_config.min_order_size_usd = float(min_order)

	def get_api_credentials(self) -> Dict[str, str]:
		"""Get API credentials from environment variables.

		Returns:
		    Dict containing api_key and either api_secret or private_key_path

		Raises:
		    ValueError: If required credentials are missing
		"""
		if self.environment == Environment.PAPER:
			# Paper trading doesn't need real credentials
			return {
				'api_key': 'paper_key_for_testing_purposes_long_enough',
				'api_secret': 'paper_secret_for_testing_purposes_long_enough',
			}

		api_key = os.getenv('BINANCE_API_KEY')
		api_secret = os.getenv('BINANCE_API_SECRET')
		private_key_path = os.getenv('BINANCE_PRIVATE_KEY_PATH')

		if not api_key:
			raise ValueError(
				f'Missing BINANCE_API_KEY for {self.environment.value} environment.'
			)

		# Support both authentication methods
		if private_key_path:
			# Ed25519 private key authentication
			return {'api_key': api_key, 'private_key_path': private_key_path}
		elif api_secret:
			# HMAC-SHA256 authentication
			return {'api_key': api_key, 'api_secret': api_secret}
		else:
			raise ValueError(
				f'Missing authentication credentials for {self.environment.value}. '
				'Set either BINANCE_API_SECRET or BINANCE_PRIVATE_KEY_PATH environment variable.'
			)

	def is_testnet(self) -> bool:
		"""Check if running in testnet mode."""
		return self.environment == Environment.TESTNET

	def is_paper_trading(self) -> bool:
		"""Check if running in paper trading mode."""
		return self.environment == Environment.PAPER

	def validate_config(self) -> bool:
		"""Validate current configuration.

		Returns:
		    True if configuration is valid

		Raises:
		    ValueError: If configuration is invalid
		"""
		# Validate trading limits
		if self.trading_config.max_position_size_usd <= 0:
			raise ValueError('Max position size must be positive')

		if self.trading_config.min_order_size_usd <= 0:
			raise ValueError('Min order size must be positive')

		if (
			self.trading_config.slippage_tolerance < 0
			or self.trading_config.slippage_tolerance > 0.1
		):
			raise ValueError('Slippage tolerance must be between 0 and 0.1 (10%)')

		# Validate API credentials (except for paper trading)
		if not self.is_paper_trading():
			self.get_api_credentials()

		logger.info('Configuration validation passed')
		return True

	def to_dict(self) -> Dict[str, Any]:
		"""Export configuration as dictionary."""
		return {
			'environment': self.environment.value,
			'endpoints': {
				'rest_base': self.endpoints.rest_base,
				'websocket_base': self.endpoints.websocket_base,
				'websocket_stream': self.endpoints.websocket_stream,
			},
			'rate_limits': {
				'requests_per_minute': self.rate_limits.requests_per_minute,
				'orders_per_10_seconds': self.rate_limits.orders_per_10_seconds,
				'orders_per_24_hours': self.rate_limits.orders_per_24_hours,
			},
			'trading_config': {
				'max_position_size_usd': self.trading_config.max_position_size_usd,
				'max_daily_loss_usd': self.trading_config.max_daily_loss_usd,
				'min_order_size_usd': self.trading_config.min_order_size_usd,
				'slippage_tolerance': self.trading_config.slippage_tolerance,
			},
		}
