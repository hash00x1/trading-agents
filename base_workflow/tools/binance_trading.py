"""
Binance Trading Tools for Crypto Agents

This module provides trading functions that integrate with Binance
through the crypto_agents_adapter, replacing the mock trading functions.
"""

import asyncio
import atexit
import logging
from typing import Optional
from langchain_core.tools import tool
from pathlib import Path

# Import the adapter
import sys
import os

sys.path.append(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from binance_wallet_integration.crypto_agents_adapter import (
	CryptoAgentsAdapter,
	run_sync_operation,
)
from binance_wallet_integration import Environment
from base_workflow.config.binance_config import binance_config

logger = logging.getLogger(__name__)

# Global adapter instance
_adapter: Optional[CryptoAgentsAdapter] = None


def get_adapter() -> CryptoAgentsAdapter:
	"""Get or create the global Binance adapter instance."""
	global _adapter

	if _adapter is None:
		if binance_config.is_live_trading_enabled():
			logger.info(
				f'Initializing Binance adapter for {binance_config.get_environment_name()}'
			)
			_adapter = run_sync_operation(
				CryptoAgentsAdapter(binance_config.environment).__aenter__()
			)
		else:
			logger.info('Live trading disabled, using paper mode')
			_adapter = run_sync_operation(
				CryptoAgentsAdapter(Environment.PAPER).__aenter__()
			)

	return _adapter


async def cleanup_adapter():
	"""Clean up the global adapter."""
	global _adapter
	if _adapter:
		await _adapter.cleanup()
		_adapter = None


def _cleanup_on_exit():
	"""Cleanup function to be called on module exit."""
	global _adapter
	if _adapter:
		try:
			# Try to run cleanup in the current event loop if available
			loop = asyncio.get_event_loop()
			if not loop.is_closed():
				loop.run_until_complete(_adapter.cleanup())
		except Exception:
			# If we can't use the current loop, create a new one
			try:
				asyncio.run(_adapter.cleanup())
			except Exception:
				# Last resort: just set to None to avoid hanging references
				logger.warning('Could not properly cleanup adapter, setting to None')
		finally:
			_adapter = None


# Register cleanup function to be called on module exit
atexit.register(_cleanup_on_exit)


@tool
def binance_buy(
	slug: str, amount: float, price: float, remaining_cryptos: float
) -> str:
	"""
	Execute a BUY order through Binance integration.

	Args:
	    slug: Crypto slug (e.g., 'bitcoin', 'ethereum')
	    amount: Amount to buy
	    price: Current market price
	    remaining_cryptos: Expected remaining crypto balance after trade

	Returns:
	    Execution result message
	"""
	try:
		if not binance_config.is_live_trading_enabled():
			# Fall back to paper trading
			logger.info(f'Paper trading: BUY {amount} {slug} @ ${price}')
			return _paper_buy(slug, amount, price, remaining_cryptos)

		adapter = get_adapter()

		# Validate order size
		order_value_usd = amount * price
		if order_value_usd < binance_config.min_order_size_usd:
			return f'Order too small: ${order_value_usd:.2f} < ${binance_config.min_order_size_usd} minimum'

		if order_value_usd > binance_config.max_position_size_usd:
			return f'Order too large: ${order_value_usd:.2f} > ${binance_config.max_position_size_usd} maximum'

		# Execute the order
		result = run_sync_operation(
			adapter.execute_buy_order(slug, amount, price, remaining_cryptos)
		)

		logger.info(f'Binance BUY executed: {result}')
		return result

	except Exception as e:
		error_msg = f'Binance BUY failed for {slug}: {str(e)}'
		logger.error(error_msg)

		# NO PAPER TRADING FALLBACK IN LIVE MODE
		if binance_config.is_live_trading_enabled():
			raise Exception(f'Live trading BUY failed for {slug}: {str(e)}')
		else:
			# Only use paper trading if explicitly in paper mode
			return _paper_buy(slug, amount, price, remaining_cryptos)


@tool
def binance_sell(
	slug: str, amount: float, price: float, remaining_dollar: float
) -> str:
	"""
	Execute a SELL order through Binance integration.

	Args:
	    slug: Crypto slug (e.g., 'bitcoin', 'ethereum')
	    amount: Amount to sell
	    price: Current market price
	    remaining_dollar: Expected remaining dollar balance after trade

	Returns:
	    Execution result message
	"""
	try:
		if not binance_config.is_live_trading_enabled():
			# Fall back to paper trading
			logger.info(f'Paper trading: SELL {amount} {slug} @ ${price}')
			return _paper_sell(slug, amount, price, remaining_dollar)

		adapter = get_adapter()

		# Validate order size
		order_value_usd = amount * price
		if order_value_usd < binance_config.min_order_size_usd:
			return f'Order too small: ${order_value_usd:.2f} < ${binance_config.min_order_size_usd} minimum'

		# Execute the order
		result = run_sync_operation(
			adapter.execute_sell_order(slug, amount, price, remaining_dollar)
		)

		logger.info(f'Binance SELL executed: {result}')
		return result

	except Exception as e:
		error_msg = f'Binance SELL failed for {slug}: {str(e)}'
		logger.error(error_msg)

		# NO PAPER TRADING FALLBACK IN LIVE MODE
		if binance_config.is_live_trading_enabled():
			raise Exception(f'Live trading SELL failed for {slug}: {str(e)}')
		else:
			# Only use paper trading if explicitly in paper mode
			return _paper_sell(slug, amount, price, remaining_dollar)


@tool
def binance_hold(slug: str) -> str:
	"""
	Execute a HOLD action (no trade).

	Args:
	    slug: Crypto slug

	Returns:
	    Hold message
	"""
	if binance_config.is_live_trading_enabled():
		adapter = get_adapter()
		result = adapter.execute_hold_order(slug)
		logger.info(f'Binance HOLD: {result}')
		return result
	else:
		return _paper_hold(slug)


def get_account_balances() -> dict:
	"""Get current account balances from Binance."""
	try:
		if not binance_config.is_live_trading_enabled():
			return {'message': 'Paper trading mode - no real balances'}

		adapter = get_adapter()
		balances = run_sync_operation(adapter.get_account_balances())
		return balances

	except Exception as e:
		logger.error(f'Failed to get account balances: {e}')
		return {'error': str(e)}


def get_real_time_price_binance(token: str) -> float:
	"""Get real-time price from Binance."""
	try:
		if not binance_config.is_live_trading_enabled():
			# Use existing price API for paper trading mode
			from base_workflow.tools.api_price import get_real_time_price

			return get_real_time_price(token)

		adapter = get_adapter()
		price = run_sync_operation(adapter.get_real_time_price(token))
		return price

	except Exception as e:
		logger.error(f'Failed to get Binance price for {token}: {e}')

		# NO FALLBACK IN LIVE MODE - must use real Binance prices
		if binance_config.is_live_trading_enabled():
			raise Exception(
				f'Live trading requires real Binance price for {token}: {str(e)}'
			)
		else:
			# Only fallback if in paper trading mode
			from base_workflow.tools.api_price import get_real_time_price

			return get_real_time_price(token)


# Paper trading fallback functions
def _paper_buy(slug: str, amount: float, price: float, remaining_cryptos: float) -> str:
	"""Paper trading buy function."""
	from datetime import datetime
	import sqlite3

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

	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_cryptos, remaining_dollar) VALUES (?, 'buy', ?, ?, ?, ?, 0.0)",
		(timestamp, slug, amount, price, remaining_cryptos),
	)
	conn.commit()
	conn.close()
	return f'[PAPER] Executed BUY for {slug} | {amount} @ ${price}'


def _paper_sell(slug: str, amount: float, price: float, remaining_dollar: float) -> str:
	"""Paper trading sell function."""
	from datetime import datetime
	import sqlite3

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

	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_cryptos, remaining_dollar) VALUES (?, 'sell', ?, ?, ?, 0.0, ?)",
		(timestamp, slug, amount, price, remaining_dollar),
	)
	conn.commit()
	conn.close()
	return f'[PAPER] Executed SELL for {slug} | {amount} @ ${price}'


def _paper_hold(slug: str) -> str:
	"""Paper trading hold function."""
	return f'[PAPER] HOLD: No trade executed for {slug}. Position unchanged.'


# Utility function for status
def get_trading_status() -> dict:
	"""Get current trading status and configuration."""
	status = {
		'environment': binance_config.get_environment_name(),
		'live_trading_enabled': binance_config.is_live_trading_enabled(),
		'max_position_size_usd': binance_config.max_position_size_usd,
		'min_order_size_usd': binance_config.min_order_size_usd,
	}

	if binance_config.is_live_trading_enabled() and _adapter:
		try:
			status.update(run_sync_operation(_adapter.get_adapter_status()))
		except Exception as e:
			status['adapter_error'] = str(e)

	return status
