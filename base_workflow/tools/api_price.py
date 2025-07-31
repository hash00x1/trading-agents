import os
import pandas as pd

from base_workflow.data.cache import get_cache
from base_workflow.data.models import (
	Price,
)
import san
import ccxt


# Global cache instance
_cache = get_cache()


def get_prices(
	slug: str, start_date: str, end_date: str, time_interval: str
) -> list[Price]:
	"""Fetch price data from cache or API."""

	# If not in cache or no data in range, fetch from API
	if api_key := os.environ.get('SANPY_APIKEY'):
		san.ApiConfig.api_key = api_key

	df = san.get(slug, from_date=start_date, to_date=end_date, interval=time_interval)
	df_renamed = df.rename(
		columns={
			'openPriceUsd': 'open',
			'closePriceUsd': 'close',
			'highPriceUsd': 'high',
			'lowPriceUsd': 'low',
			'volume': 'volume',
		}
	)
	df_renamed = df_renamed.reset_index().rename(columns={'datetime': 'time'})
	prices = [
		Price(**{**row, 'time': row['time'].isoformat()})
		for row in df_renamed.to_dict(orient='records')
	]

	_cache.set_prices(slug, [p.model_dump() for p in prices])
	return prices


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
	"""Convert prices to a DataFrame."""
	df = pd.DataFrame([p.model_dump() for p in prices])
	df['Date'] = pd.to_datetime(df['time'])
	df.set_index('Date', inplace=True)
	numeric_cols = ['open', 'close', 'high', 'low', 'volume']
	for col in numeric_cols:
		df[col] = pd.to_numeric(df[col], errors='coerce')
	df.sort_index(inplace=True)
	return df


# Update the get_price_data function to use the new functions
def get_price_data(slug: str, start_date: str, end_date: str) -> pd.DataFrame:
	prices = get_prices(slug, start_date, end_date, '4h')
	return prices_to_df(prices)


def get_real_time_price(symbol: str, exchange_id: str = 'binance') -> float:
	"""
	Get the real-time price (latest traded price) of a given trading pair.

	Parameters:
	    symbol (str): Trading pair symbol, e.g., 'ETH/USDT'.
	    exchange_id (str): Exchange identifier, default is 'binance'

	Returns:
	    float: Latest traded price, ready for numerical calculations
	"""
	exchange_class = getattr(ccxt, exchange_id)
	exchange = exchange_class(
		{
			'enableRateLimit': True,
			'timeout': 10000,  # in milliseconds (10 seconds)
		}
	)

	ticker = exchange.fetch_ticker(f'{symbol}/USDT')

	return float(ticker['last'])


if __name__ == '__main__':
	price = get_real_time_price('ETH')
	print(f'当前 ETH/USDT 实时价格：{price} USDT')

# Example usage
# slug = 'ohlcv/bitcoin'
# start_date = '2024-06-07'
# end_date = '2025-05-08'
# # # end_date = datetime.utcnow().date().isoformat()
# end_date = "2025-05-08"
# end_dt = datetime.strptime(end_date, "%Y-%m-%d")
# start_dt = end_dt - timedelta(weeks=2)
# start_date = start_dt.date().isoformat()

# prices_df = get_price_data(slug, start_date, end_date)
# print(prices_df.head())
