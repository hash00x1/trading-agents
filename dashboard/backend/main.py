"""
Professional Trading Dashboard API
FastAPI backend for crypto trading analytics and portfolio management
"""

import asyncio
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import pandas as pd
import uvicorn
from fastapi import (
	FastAPI,
	HTTPException,
	WebSocket,
	WebSocketDisconnect,
	BackgroundTasks,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directories to path for imports
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from base_workflow.tools.binance_trading import (
	get_account_balances,
	get_real_time_price_binance,
)
from base_workflow.config.binance_config import binance_config


class ConnectionManager:
	"""WebSocket connection manager for real-time updates"""

	def __init__(self):
		self.active_connections: List[WebSocket] = []

	async def connect(self, websocket: WebSocket):
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket):
		self.active_connections.remove(websocket)

	async def broadcast(self, message: dict):
		for connection in self.active_connections:
			try:
				await connection.send_text(json.dumps(message))
			except:
				pass


manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""App lifespan manager"""
	logger.info('Starting Trading Dashboard API')
	# Start background tasks
	asyncio.create_task(price_update_task())
	yield
	logger.info('Shutting down Trading Dashboard API')


app = FastAPI(
	title='Crypto Trading Dashboard',
	description='Professional trading analytics and portfolio management interface',
	version='1.0.0',
	lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		'http://localhost:3000',
		'http://localhost:5173',
	],  # React dev servers
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


# Pydantic models
class TradeRecord(BaseModel):
	id: int
	timestamp: str
	action: Optional[str]
	slug: str
	amount: float
	price: float
	remaining_cryptos: float
	remaining_dollar: float


class PortfolioSummary(BaseModel):
	total_usd_value: float
	total_pnl: float
	total_pnl_percentage: float
	positions: Dict[str, Dict[str, Any]]
	last_updated: str


class PerformanceMetrics(BaseModel):
	period: str
	pnl: float
	pnl_percentage: float
	trades_count: int
	win_rate: float
	sharpe_ratio: Optional[float]
	max_drawdown: float


class PriceData(BaseModel):
	slug: str
	current_price: float
	change_24h: Optional[float]
	timestamp: str


class WebhookRequest(BaseModel):
	action: str  # 'buy', 'sell', 'hold'
	slug: str
	amount: Optional[float] = None
	price: Optional[float] = None


# Asset mapping for Binance symbols to crypto slugs
asset_to_slug_mapping = {
	'btc': 'bitcoin',
	'eth': 'ethereum', 
	'doge': 'dogecoin',
	'pepe': 'pepe',
	'usdt': 'tether',
	'usdc': 'usd-coin',
	'bnb': 'binancecoin',
	'ada': 'cardano',
	'sol': 'solana',
	'xrp': 'ripple',
	'dot': 'polkadot',
	'avax': 'avalanche-2',
	'link': 'chainlink',
	'matic': 'matic-network',
	'ltc': 'litecoin',
}

# Helper functions
def get_db_path(slug: str) -> Path:
	"""Get database path for a specific crypto"""
	# Adjust path relative to project root
	project_root = Path(__file__).parent.parent.parent
	return project_root / f'base_workflow/outputs/{slug}_trades.db'


def get_available_cryptos() -> List[str]:
	"""Get list of available crypto databases"""
	# Adjust path relative to project root
	project_root = Path(__file__).parent.parent.parent
	output_dir = project_root / 'base_workflow/outputs'
	if not output_dir.exists():
		return []

	cryptos = []
	for db_file in output_dir.glob('*_trades.db'):
		slug = db_file.stem.replace('_trades', '')
		cryptos.append(slug)

	return sorted(cryptos)


async def get_trades_data(slug: str, limit: Optional[int] = None) -> List[TradeRecord]:
	"""Get trades data for a specific crypto"""
	db_path = get_db_path(slug)

	if not db_path.exists():
		return []

	try:
		conn = sqlite3.connect(db_path)
		query = 'SELECT * FROM trades ORDER BY timestamp DESC'
		if limit:
			query += f' LIMIT {limit}'

		df = pd.read_sql_query(query, conn)
		conn.close()

		trades = []
		for _, row in df.iterrows():
			# Handle NaN values by converting to None or 0
			trades.append(
				TradeRecord(
					id=int(row['id']) if pd.notna(row['id']) else 0,
					timestamp=str(row['timestamp'])
					if pd.notna(row['timestamp'])
					else '',
					action=str(row['action']) if pd.notna(row['action']) else None,
					slug=str(row['slug']) if pd.notna(row['slug']) else '',
					amount=float(row['amount']) if pd.notna(row['amount']) else 0.0,
					price=float(row['price']) if pd.notna(row['price']) else 0.0,
					remaining_cryptos=float(row['remaining_cryptos'])
					if pd.notna(row['remaining_cryptos'])
					else 0.0,
					remaining_dollar=float(row['remaining_dollar'])
					if pd.notna(row['remaining_dollar'])
					else 0.0,
				)
			)

		return trades
	except Exception as e:
		logger.error(f'Error getting trades for {slug}: {e}')
		return []


async def calculate_pnl(slug: str, period_days: int = 1) -> Dict[str, float]:
	"""Calculate PnL for a specific period"""
	trades = await get_trades_data(slug)

	if not trades:
		return {'pnl': 0.0, 'pnl_percentage': 0.0, 'trades_count': 0}

	# Filter trades by period
	cutoff_date = datetime.now() - timedelta(days=period_days)
	period_trades = [
		t
		for t in trades
		if datetime.fromisoformat(t.timestamp.replace('Z', '+00:00')) > cutoff_date
	]

	if not period_trades:
		return {'pnl': 0.0, 'pnl_percentage': 0.0, 'trades_count': 0}

	# Get current price
	try:
		current_price = get_real_time_price_binance(trades[0].slug)
	except:
		current_price = trades[0].price

	# Calculate PnL
	latest_trade = trades[0]
	current_value = (
		latest_trade.remaining_cryptos * current_price + latest_trade.remaining_dollar
	)

	# Find initial value for the period
	if len(period_trades) > 0:
		oldest_trade = period_trades[-1]
		initial_value = (
			oldest_trade.remaining_cryptos * oldest_trade.price
			+ oldest_trade.remaining_dollar
		)
	else:
		initial_value = current_value

	pnl = current_value - initial_value
	pnl_percentage = (pnl / initial_value * 100) if initial_value > 0 else 0.0

	return {
		'pnl': pnl,
		'pnl_percentage': pnl_percentage,
		'trades_count': len(period_trades),
		'current_value': current_value,
		'initial_value': initial_value,
	}


async def get_local_portfolio_summary():
	"""Get portfolio summary from local database (paper trading mode only)"""
	cryptos = get_available_cryptos()

	total_usd_value = 0.0
	total_pnl = 0.0
	positions = {}

	for slug in cryptos:
		trades = await get_trades_data(slug, limit=1)

		if trades:
			latest_trade = trades[0]

			# Get current price (fallback to historical if real price fails)
			try:
				current_price = get_real_time_price_binance(slug)
			except:
				current_price = latest_trade.price if latest_trade.price > 0 else 1.0

			# Calculate position value
			crypto_value = latest_trade.remaining_cryptos * current_price
			total_value = crypto_value + latest_trade.remaining_dollar
			total_usd_value += total_value

			# Calculate 24h PnL
			pnl_data = await calculate_pnl(slug, period_days=1)
			total_pnl += pnl_data['pnl']

			positions[slug] = {
				'crypto_balance': latest_trade.remaining_cryptos,
				'usd_balance': latest_trade.remaining_dollar,
				'current_price': current_price,
				'crypto_value': crypto_value,
				'total_value': total_value,
				'pnl_24h': pnl_data['pnl'],
				'pnl_24h_percentage': pnl_data['pnl_percentage'],
				'last_action': latest_trade.action,
				'last_trade_time': latest_trade.timestamp,
				'source': 'local_database'
			}

	total_pnl_percentage = (
		(total_pnl / total_usd_value * 100) if total_usd_value > 0 else 0.0
	)

	return PortfolioSummary(
		total_usd_value=total_usd_value,
		total_pnl=total_pnl,
		total_pnl_percentage=total_pnl_percentage,
		positions=positions,
		last_updated=datetime.now().isoformat(),
	)


# API Endpoints


@app.get('/')
async def root():
	"""Health check endpoint"""
	return {
		'message': 'Crypto Trading Dashboard API',
		'version': '1.0.0',
		'status': 'healthy',
		'trading_mode': binance_config.get_environment_name(),
	}


@app.get('/api/portfolio/summary', response_model=PortfolioSummary)
async def get_portfolio_summary():
	"""Get complete portfolio summary with REAL Binance account balances"""
	
	# First, get real Binance account balances
	real_balances = {}
	total_usd_value = 0.0
	
	try:
		# Get real account balances from Binance
		binance_balances = get_account_balances()
		
		if isinstance(binance_balances, dict) and 'error' not in binance_balances:
			# Process real Binance balances
			for asset, balance_info in binance_balances.items():
				if isinstance(balance_info, dict) and balance_info.get('total', 0) > 0:
					# Get current USD price for the asset
					try:
						if asset.upper() == 'USDT' or asset.upper() == 'USD':
							current_price = 1.0
						else:
							# Convert asset names to slugs for price lookup
							slug = asset_to_slug_mapping.get(asset.lower(), asset.lower())
							current_price = get_real_time_price_binance(slug)
						
						crypto_balance = balance_info['total']
						crypto_value = crypto_balance * current_price
						total_usd_value += crypto_value
						
						real_balances[asset.lower()] = {
							'crypto_balance': crypto_balance,
							'usd_balance': 0.0,  # All value is in crypto for real balances
							'current_price': current_price,
							'crypto_value': crypto_value,
							'total_value': crypto_value,
							'pnl_24h': 0.0,  # Calculate from trade history
							'pnl_24h_percentage': 0.0,
							'last_action': 'real_balance',
							'last_trade_time': datetime.now().isoformat(),
							'source': 'binance_live'
						}
						
					except Exception as price_error:
						logger.warning(f"Could not get price for {asset}: {price_error}")
						continue
		
		# If we have real balances, use them; otherwise fall back to local data for development
		if real_balances:
			logger.info(f"Using REAL Binance balances: {len(real_balances)} assets, ${total_usd_value:.2f} total")
			return PortfolioSummary(
				total_usd_value=total_usd_value,
				total_pnl=0.0,  # Would need historical data to calculate properly
				total_pnl_percentage=0.0,
				positions=real_balances,
				last_updated=datetime.now().isoformat(),
			)
			
	except Exception as e:
		logger.error(f"Failed to get real Binance balances: {e}")
		
		# STOP PAPER TRADING FALLBACK FOR LIVE MODE
		if binance_config.is_live_trading_enabled():
			raise HTTPException(
				status_code=503, 
				detail=f"Live trading mode enabled but cannot access Binance account: {str(e)}"
			)
	
	# Only use local data if in paper trading mode
	if not binance_config.is_live_trading_enabled():
		logger.info("Paper trading mode - using local database balances")
		return await get_local_portfolio_summary()
	else:
		raise HTTPException(
			status_code=503, 
			detail="Live trading mode enabled but Binance account access failed"
		)


@app.get('/api/performance/{slug}')
async def get_performance_metrics(slug: str, periods: str = '1,7,30'):
	"""Get performance metrics for different time periods"""
	period_list = [int(p) for p in periods.split(',')]
	metrics = []

	for period_days in period_list:
		pnl_data = await calculate_pnl(slug, period_days)

		period_name = f'{period_days}d' if period_days < 30 else f'{period_days // 30}M'

		metrics.append(
			PerformanceMetrics(
				period=period_name,
				pnl=pnl_data['pnl'],
				pnl_percentage=pnl_data['pnl_percentage'],
				trades_count=pnl_data['trades_count'],
				win_rate=0.0,  # Calculate based on winning trades
				sharpe_ratio=None,  # Requires more complex calculation
				max_drawdown=0.0,  # Requires historical analysis
			)
		)

	return metrics


@app.get('/api/trades/{slug}')
async def get_trades(slug: str, limit: int = 50):
	"""Get trade history for a specific crypto"""
	return await get_trades_data(slug, limit)


@app.get('/api/cryptos')
async def get_cryptos():
	"""Get list of available cryptocurrencies"""
	return {'cryptos': get_available_cryptos()}


@app.get('/api/prices')
async def get_current_prices():
	"""Get current prices for all tracked cryptos"""
	cryptos = get_available_cryptos()
	prices = {}

	for slug in cryptos:
		try:
			price = get_real_time_price_binance(slug)
			prices[slug] = {
				'current_price': price,
				'timestamp': datetime.now().isoformat(),
			}
		except Exception as e:
			logger.error(f'Error getting price for {slug}: {e}')
			prices[slug] = {
				'current_price': 0.0,
				'timestamp': datetime.now().isoformat(),
				'error': str(e),
			}

	return prices


@app.get('/api/balances')
async def get_binance_balances():
	"""Get real Binance account balances"""
	try:
		balances = get_account_balances()
		return {'balances': balances, 'timestamp': datetime.now().isoformat()}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'Failed to get balances: {str(e)}')


# WebSocket endpoint for real-time updates
@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
	await manager.connect(websocket)
	try:
		while True:
			# Keep connection alive and handle messages
			data = await websocket.receive_text()
			message = json.loads(data)

			if message.get('type') == 'subscribe':
				# Handle subscription requests
				await websocket.send_text(
					json.dumps({'type': 'subscribed', 'status': 'connected'})
				)
	except WebSocketDisconnect:
		manager.disconnect(websocket)


# Webhook endpoints for n8n.io integration
@app.post('/webhook/trade')
async def webhook_trade(request: WebhookRequest, background_tasks: BackgroundTasks):
	"""Webhook endpoint for external trading signals (n8n.io integration)"""
	try:
		logger.info(f'Webhook trade request: {request}')

		# Validate request
		if request.action not in ['buy', 'sell', 'hold']:
			raise HTTPException(status_code=400, detail='Invalid action')

		if request.slug not in get_available_cryptos():
			raise HTTPException(status_code=400, detail='Unknown cryptocurrency')

		# For buy/sell actions, validate amount
		if request.action in ['buy', 'sell'] and not request.amount:
			raise HTTPException(
				status_code=400, detail='Amount required for buy/sell actions'
			)

		# Schedule trade execution in background
		background_tasks.add_task(execute_webhook_trade, request)

		return {
			'status': 'accepted',
			'message': f'Trade {request.action} for {request.slug} scheduled',
			'timestamp': datetime.now().isoformat(),
		}

	except Exception as e:
		logger.error(f'Webhook error: {e}')
		raise HTTPException(status_code=500, detail=str(e))


async def execute_webhook_trade(request: WebhookRequest):
	"""Execute trade from webhook request"""
	try:
		# Import trading functions
		from base_workflow.tools.binance_trading import (
			binance_buy,
			binance_sell,
			binance_hold,
		)

		if request.action == 'buy':
			result = binance_buy.invoke(
				{
					'slug': request.slug,
					'amount': request.amount,
					'price': request.price or get_real_time_price_binance(request.slug),
					'remaining_cryptos': request.amount,
				}
			)
		elif request.action == 'sell':
			result = binance_sell.invoke(
				{
					'slug': request.slug,
					'amount': request.amount,
					'price': request.price or get_real_time_price_binance(request.slug),
					'remaining_dollar': request.amount
					* (request.price or get_real_time_price_binance(request.slug)),
				}
			)
		else:  # hold
			result = binance_hold.invoke({'slug': request.slug})

		# Broadcast update to connected clients
		await manager.broadcast(
			{
				'type': 'trade_executed',
				'slug': request.slug,
				'action': request.action,
				'result': result,
				'timestamp': datetime.now().isoformat(),
			}
		)

		logger.info(f'Webhook trade executed: {result}')

	except Exception as e:
		logger.error(f'Webhook trade execution failed: {e}')
		await manager.broadcast(
			{
				'type': 'trade_error',
				'slug': request.slug,
				'action': request.action,
				'error': str(e),
				'timestamp': datetime.now().isoformat(),
			}
		)


# Background tasks
async def price_update_task():
	"""Background task to broadcast price updates"""
	while True:
		try:
			await asyncio.sleep(30)  # Update every 30 seconds

			prices = await get_current_prices()
			await manager.broadcast(
				{
					'type': 'price_update',
					'data': prices,
					'timestamp': datetime.now().isoformat(),
				}
			)

		except Exception as e:
			logger.error(f'Price update task error: {e}')
			await asyncio.sleep(60)  # Wait longer on error


if __name__ == '__main__':
	uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True, log_level='info')
