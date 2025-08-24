"""
Binance Wallet Integration Module

Professional, secure integration with Binance API for real-time crypto trading.
Supports both testnet and mainnet environments with comprehensive rate limiting,
error handling, and security measures.

Architecture:
- BinanceClient: Main API client with rate limiting
- WebSocketManager: Real-time data streams
- OrderManager: Trade execution with safety checks
- SecurityManager: API key management and validation
- ConfigManager: Environment and configuration handling
"""

from .client import BinanceClient
from .websocket_manager import WebSocketManager
from .order_manager import OrderManager
from .security import SecurityManager
from .config import ConfigManager, Environment
from .rate_limiter import RateLimitManager

__version__ = '1.0.0'
__author__ = 'crypto_agents team'

__all__ = [
	'BinanceClient',
	'WebSocketManager',
	'OrderManager',
	'SecurityManager',
	'ConfigManager',
	'Environment',
	'RateLimitManager',
]

