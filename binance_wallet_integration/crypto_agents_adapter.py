"""
Crypto Agents Adapter for Binance Integration

Adapts the Binance wallet integration to work seamlessly with the existing
crypto_agents portfolio management system.
"""

import asyncio
import logging
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .client import BinanceClient
from .order_manager import OrderManager
from .config import ConfigManager, Environment

logger = logging.getLogger(__name__)


class CryptoAgentsAdapter:
	"""Adapter to integrate Binance wallet with crypto_agents system."""

	def __init__(self, environment: Environment = Environment.TESTNET):
		"""Initialize the adapter.

		Args:
		    environment: Trading environment (TESTNET, MAINNET, or PAPER)
		"""
		self.environment = environment
		self.config = ConfigManager(environment)
		self.client: Optional[BinanceClient] = None
		self.order_manager: Optional[OrderManager] = None

		# Slug to token mapping (crypto_agents slug -> token ticker)
		self.slug_to_token_mapping = {
			'bitcoin': 'BTC',
			'ethereum': 'ETH',
			'pepe': 'PEPE',
			'dogecoin': 'DOGE',
			'tether': 'USDT',
			'litecoin': 'LTC',
			'binancecoin': 'BNB',
			'tron': 'TRX',
			'ripple': 'XRP',
			'neo': 'NEO',
			'qtum': 'QTUM',
			'gas': 'GAS',
			'loopring': 'LRC',
			'0x': 'ZRX',
			'kyber-network': 'KNC',
			'iota': 'IOTA',
			'chainlink': 'LINK',
		}

		# Token to trading pair mapping (token ticker -> Binance trading pair)
		self.token_to_pair_mapping = {
			'BTC': 'BTCUSDT',
			'ETH': 'ETHUSDT',
			'PEPE': 'PEPEUSDT',
			'DOGE': 'DOGEUSDT',
			'LTC': 'LTCUSDT',
			'BNB': 'BNBUSDT',
			'TRX': 'TRXUSDT',
			'XRP': 'XRPUSDT',
			'NEO': 'NEOUSDT',
			'QTUM': 'QTUMUSDT',
			'GAS': 'GASUSDT',
			'LRC': 'LRCUSDT',
			'ZRX': 'ZRXUSDT',
			'KNC': 'KNCUSDT',
			'IOTA': 'IOTAUSDT',
			'LINK': 'LINKUSDT',
			'USDT': 'USDT',  # Base currency (no pair needed)
		}

		logger.info(f'CryptoAgentsAdapter initialized for {environment.value}')

	async def __aenter__(self):
		"""Async context manager entry."""
		await self.initialize()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		"""Async context manager exit."""
		await self.cleanup()

	async def initialize(self) -> None:
		"""Initialize the adapter and connections."""
		try:
			# Initialize Binance client
			self.client = BinanceClient(self.config)
			await self.client._ensure_session()

			# Initialize order manager
			self.order_manager = OrderManager(self.client, self.config)
			await self.order_manager.initialize()

			logger.info('CryptoAgentsAdapter initialized successfully')

		except Exception as e:
			logger.error(f'Failed to initialize adapter: {e}')
			raise

	async def cleanup(self) -> None:
		"""Clean up resources."""
		if self.client:
			await self.client.close()

		logger.info('CryptoAgentsAdapter cleaned up')

	def _slug_to_token(self, slug: str) -> str:
		"""Convert crypto_agents slug to token ticker.

		Args:
		    slug: Crypto slug (e.g., 'bitcoin', 'ethereum')

		Returns:
		    Token ticker (e.g., 'BTC', 'ETH')
		"""
		return self.slug_to_token_mapping.get(slug.lower(), slug.upper())

	def _token_to_pair(self, token: str) -> str:
		"""Convert token ticker to Binance trading pair.

		Args:
		    token: Token ticker (e.g., 'BTC', 'ETH')

		Returns:
		    Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
		"""
		token_upper = token.upper()
		if token_upper in self.token_to_pair_mapping:
			return self.token_to_pair_mapping[token_upper]
		else:
			# Default: append USDT for unknown tokens
			return f'{token_upper}USDT'

	def _convert_symbol(self, crypto_agents_symbol: str) -> str:
		"""Convert crypto_agents symbol to Binance trading pair format.

		This method handles both slugs and tokens for backward compatibility.

		Args:
		    crypto_agents_symbol: Symbol in crypto_agents format (e.g., 'BTC' or 'bitcoin')

		Returns:
		    Trading pair in Binance format (e.g., 'BTCUSDT')
		"""
		# If it's a slug, convert to token first
		if crypto_agents_symbol.lower() in self.slug_to_token_mapping:
			token = self._slug_to_token(crypto_agents_symbol)
		else:
			# Assume it's already a token ticker
			token = crypto_agents_symbol.upper()

		# Convert token to trading pair
		return self._token_to_pair(token)

	def _token_to_slug(self, token: str) -> str:
		"""Convert token symbol to crypto_agents slug.

		Args:
		    token: Token symbol (e.g., 'BTC')

		Returns:
		    Crypto slug (e.g., 'bitcoin')
		"""
		# Reverse lookup in the slug_to_token_mapping
		token_upper = token.upper()
		for slug, mapped_token in self.slug_to_token_mapping.items():
			if mapped_token == token_upper:
				return slug

		# Default fallback
		return token.lower()

	async def get_real_time_price(self, token: str) -> float:
		"""Get real-time price for a token (compatible with existing crypto_agents interface).

		Args:
		    token: Token symbol (e.g., 'BTC', 'ETH')

		Returns:
		    Current price in USDT
		"""
		if not self.client:
			raise RuntimeError('Adapter not initialized')

		symbol = self._convert_symbol(token)

		try:
			price_data = await self.client.get_symbol_price(symbol)
			price = float(price_data['price'])

			logger.debug(f'Got price for {token}: ${price}')
			return price

		except Exception as e:
			logger.error(f'Failed to get price for {token}: {e}')
			raise

	async def execute_buy_order(
		self, slug: str, amount: float, price: float, remaining_cryptos: float
	) -> str:
		"""Execute buy order (replaces the original buy() function).

		Args:
		    slug: Crypto slug (e.g., 'bitcoin')
		    amount: Amount to buy
		    price: Price per token
		    remaining_cryptos: Remaining crypto balance after trade

		Returns:
		    Execution result message
		"""
		if not self.order_manager:
			raise RuntimeError('Order manager not initialized')

		try:
			# Convert slug to symbol
			token = self._slug_to_token(slug)
			symbol = self._convert_symbol(token)

			# Execute market buy order
			result = await self.order_manager.buy_market(symbol, amount)

			if result.success:
				# Update crypto_agents database
				self._update_trades_database(
					slug=slug,
					action='buy',
					amount=result.filled_quantity,
					price=result.filled_price,
					remaining_cryptos=remaining_cryptos,
					remaining_dollar=0.0,
				)

				message = f'Executed BUY for {slug} | {result.filled_quantity} @ ${result.filled_price}'
				logger.info(message)
				return message
			else:
				error_msg = f'Failed to execute BUY for {slug}: {result.error_message}'
				logger.error(error_msg)
				return error_msg

		except Exception as e:
			error_msg = f'Error executing BUY for {slug}: {str(e)}'
			logger.error(error_msg)
			return error_msg

	async def execute_sell_order(
		self, slug: str, amount: float, price: float, remaining_dollar: float
	) -> str:
		"""Execute sell order (replaces the original sell() function).

		Args:
		    slug: Crypto slug (e.g., 'bitcoin')
		    amount: Amount to sell
		    price: Price per token
		    remaining_dollar: Remaining dollar balance after trade

		Returns:
		    Execution result message
		"""
		if not self.order_manager:
			raise RuntimeError('Order manager not initialized')

		try:
			# Convert slug to symbol
			token = self._slug_to_token(slug)
			symbol = self._convert_symbol(token)

			# Execute market sell order
			result = await self.order_manager.sell_market(symbol, amount)

			if result.success:
				# Update crypto_agents database
				self._update_trades_database(
					slug=slug,
					action='sell',
					amount=result.filled_quantity,
					price=result.filled_price,
					remaining_cryptos=0.0,
					remaining_dollar=remaining_dollar,
				)

				message = f'Executed SELL for {slug} | {result.filled_quantity} @ ${result.filled_price}'
				logger.info(message)
				return message
			else:
				error_msg = f'Failed to execute SELL for {slug}: {result.error_message}'
				logger.error(error_msg)
				return error_msg

		except Exception as e:
			error_msg = f'Error executing SELL for {slug}: {str(e)}'
			logger.error(error_msg)
			return error_msg

	def execute_hold_order(self, slug: str) -> str:
		"""Execute hold order (replaces the original hold() function).

		Args:
		    slug: Crypto slug

		Returns:
		    Hold message
		"""
		message = f'HOLD: No trade executed for {slug}. Position unchanged.'
		logger.info(message)
		return message

	# def _slug_to_token(self, slug: str) -> str:
	# 	"""Convert crypto_agents slug to token symbol.

	# 	Args:
	# 	    slug: Crypto slug (e.g., 'bitcoin', 'ethereum')

	# 	Returns:
	# 	    Token symbol (e.g., 'BTC', 'ETH')
	# 	"""
	# 	slug_to_token_map = {
	# 		'bitcoin': 'BTC',
	# 		'ethereum': 'ETH',
	# 		'pepe': 'PEPE',
	# 		'dogecoin': 'DOGE',
	# 		'tether': 'USDT',
	# 	}

	# 	return slug_to_token_map.get(slug.lower(), slug.upper())

	def _update_trades_database(
		self,
		slug: str,
		action: str,
		amount: float,
		price: float,
		remaining_cryptos: float,
		remaining_dollar: float,
	) -> None:
		"""Update the crypto_agents trades database.

		Args:
		    slug: Crypto slug
		    action: Trade action ('buy' or 'sell')
		    amount: Trade amount
		    price: Trade price
		    remaining_cryptos: Remaining crypto balance
		    remaining_dollar: Remaining dollar balance
		"""
		try:
			# Use the same database structure as crypto_agents
			db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
			db_path.parent.mkdir(parents=True, exist_ok=True)

			conn = sqlite3.connect(db_path)
			cursor = conn.cursor()

			# Create table if it doesn't exist
			cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    action TEXT,
                    slug TEXT,
                    amount REAL,
                    price REAL,
                    remaining_cryptos REAL,
                    remaining_dollar REAL
                )
            """)

			# Insert trade record
			timestamp = datetime.utcnow().isoformat()
			cursor.execute(
				'INSERT INTO trades (timestamp, action, slug, amount, price, remaining_cryptos, remaining_dollar) VALUES (?, ?, ?, ?, ?, ?, ?)',
				(
					timestamp,
					action,
					slug,
					amount,
					price,
					remaining_cryptos,
					remaining_dollar,
				),
			)

			conn.commit()
			conn.close()

			logger.debug(f'Updated {slug} trades database: {action} {amount} @ {price}')

		except Exception as e:
			logger.error(f'Failed to update trades database: {e}')

	async def get_account_balances(self) -> Dict[str, Dict[str, float]]:
		"""Get current account balances from Binance.

		Returns:
		    Dictionary of balances by symbol
		"""
		if not self.client:
			raise RuntimeError('Client not initialized')

		try:
			account_info = await self.client.get_account_info()
			balances = {}

			for balance in account_info.get('balances', []):
				asset = balance['asset']
				free = float(balance['free'])
				locked = float(balance['locked'])

				if free > 0 or locked > 0:
					balances[asset] = {
						'free': free,
						'locked': locked,
						'total': free + locked,
					}

			logger.info(f'Retrieved balances for {len(balances)} assets')
			return balances

		except Exception as e:
			logger.error(f'Failed to get account balances: {e}')
			raise

	async def sync_balances_with_database(self) -> Dict[str, Any]:
		"""Sync Binance balances with crypto_agents database.

		Returns:
		    Sync results
		"""
		try:
			# Get current Binance balances
			binance_balances = await self.get_account_balances()

			sync_results = {}

			# Check each supported token
			for slug, token in self.slug_to_token_mapping.items():
				if token == 'USDT':
					continue  # Skip base currency

				# Get balance from Binance
				binance_crypto = binance_balances.get(token, {}).get('total', 0)
				binance_usdt = binance_balances.get('USDT', {}).get('total', 0)

				# Get balance from database
				db_balances = self._get_database_balance(slug)

				sync_results[token] = {
					'binance_crypto': binance_crypto,
					'binance_usdt': binance_usdt,
					'database_crypto': db_balances['crypto'],
					'database_dollar': db_balances['dollar'],
					'crypto_diff': binance_crypto - db_balances['crypto'],
					'dollar_diff': binance_usdt - db_balances['dollar'],
				}

			logger.info('Balance synchronization completed')
			return sync_results

		except Exception as e:
			logger.error(f'Failed to sync balances: {e}')
			raise

	def _get_database_balance(self, slug: str) -> Dict[str, float]:
		"""Get current balance from crypto_agents database.

		Args:
		    slug: Crypto slug

		Returns:
		    Dictionary with crypto and dollar balances
		"""
		try:
			db_path = Path(f'base_workflow/outputs/{slug}_trades.db')

			if not db_path.exists():
				return {'crypto': 0.0, 'dollar': 0.0}

			conn = sqlite3.connect(db_path)
			cursor = conn.cursor()

			# Get latest balance
			cursor.execute("""
                SELECT remaining_cryptos, remaining_dollar 
                FROM trades 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)

			result = cursor.fetchone()
			conn.close()

			if result:
				return {'crypto': result[0] or 0.0, 'dollar': result[1] or 0.0}
			else:
				return {'crypto': 0.0, 'dollar': 0.0}

		except Exception as e:
			logger.error(f'Failed to get database balance for {slug}: {e}')
			return {'crypto': 0.0, 'dollar': 0.0}

	def get_adapter_status(self) -> Dict[str, Any]:
		"""Get adapter status information.

		Returns:
		    Status dictionary
		"""
		status = {
			'environment': self.environment.value,
			'initialized': self.client is not None and self.order_manager is not None,
			'config': self.config.to_dict() if self.config else None,
		}

		if self.client:
			status['client_status'] = self.client.get_status()

		if self.order_manager:
			status['trading_stats'] = self.order_manager.get_trading_stats()

		return status


# Convenience functions to replace the original crypto_agents functions


async def create_binance_adapter(
	environment: Environment = Environment.TESTNET,
) -> CryptoAgentsAdapter:
	"""Create and initialize a Binance adapter.

	Args:
	    environment: Trading environment

	Returns:
	    Initialized adapter
	"""
	adapter = CryptoAgentsAdapter(environment)
	await adapter.initialize()
	return adapter


def run_sync_operation(coro):
	"""Run async operation synchronously (for compatibility with existing sync code)."""
	try:
		loop = asyncio.get_event_loop()
		return loop.run_until_complete(coro)
	except RuntimeError:
		# No loop running, create a new one
		return asyncio.run(coro)
