import os
import pandas as pd
from typing import Tuple
from base_workflow.data.models import (
	SocialSentimentScoreValue,
)
from langchain.tools import tool
import san
import numpy as np
from scipy.stats import linregress
from openai import OpenAI
from datetime import datetime, timedelta
from langchain.agents import initialize_agent, AgentType
from base_workflow.utils.llm_config import get_llm


def _date_only(s: str) -> str:
	"""Return YYYY-MM-DD part only."""
	return str(s).split('T')[0].split(' ')[0]


def _build_system_text(slug: str, start_date: str, end_date: str) -> str:
	return (
		'ROLE: You are an on-chain analyst.\n'
		'OBJECTIVE: Report whale-related on-chain activity for the specified asset and date window ONLY.\n'
		f'ASSET: {slug}\n'
		f'DATE_WINDOW: from {start_date} to {end_date} (inclusive, format YYYY-MM-DD). Do not use data outside this window.\n\n'
		'DATA PRIORITY:\n'
		'1) Primary: On-chain data sources supporting multi-chain assets (e.g., Santiment, Glassnode, Whale Alert, Nansen, Arkham).\n'
		'   - Include Ethereum, Bitcoin, Solana, Binance Smart Chain, and popular ERC-20 tokens (e.g., USDT, USDC, PEPE).\n'
		'   - Accept contract-address-level metrics when available (e.g., for tokens like PEPE).\n'
		'2) Secondary (for context): reputable news (CoinDesk, The Block, CryptoSlate, etc.), only if it cites on-chain events directly within the time window.\n\n'
		'STRICT RULES:\n'
		'- Use only the specified asset; discard other tickers.\n'
		'- Discard sources without clear dates or outside the date window.\n'
		'- Do NOT output price/market summary or live quotes (no price tools available here).\n'
		'- If only indicative data is found (without exact values), include it in `notes`, and set numeric fields to null.\n'
		'- Include citations with URL and published date for every numeric/strong claim.\n\n'
		'- Prefer primary on-chain sources (Whale Alert, Santiment, Glassnode). Use news only if they directly cite on-chain metrics within the date window.\n\n'
		'OUTPUT: Return ONLY a JSON object matching the schema described below. No extra text.\n'
		'{\n'
		'  "status": "OK" | "NO_DATA",\n'
		'  "timeframe": {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"},\n'
		'  "asset": "string",\n'
		'  "signals": {\n'
		'    "large_tx_counts": {"gt_100k_usd": "number|null", "gt_1m_usd": "number|null"},\n'
		'    "whale_net_position_change": "number|null",\n'
		'    "exchange_netflow_whales": "number|null",\n'
		'    "notes": "string"\n'
		'  },\n'
		'  "trading_stance": {"signal": "Buy|Neutral|Sell", "confidence": "number in [0,1]"},\n'
		'  "citations": [ {"url":"string","title":"string","published_date":"YYYY-MM-DD"} ]\n'
		'}\n'
	)


@tool
def get_on_chain_openai(slug: str, curr_date: str):
	"""
	Search for on-chain whale-related activity about a token in the last 14 days.
	"""
	client = OpenAI()
	end_date = _date_only(curr_date)
	curr_dt = datetime.strptime(end_date, '%Y-%m-%d')
	start_date = (curr_dt - timedelta(days=14)).date().isoformat()
	system_text = _build_system_text(slug, start_date, end_date)

	response = client.responses.create(
		model='gpt-4.1',
		input=[
			{
				'role': 'system',
				'content': [
					{
						'type': 'input_text',
						'text': system_text,
					}
				],
			}
		],
		text={'format': {'type': 'text'}},
		tools=[
			{
				'type': 'web_search_preview',
				'user_location': {'type': 'approximate'},
				'search_context_size': 'high',
			}
		],
		temperature=0.2,
		max_output_tokens=512,
		top_p=1,
		store=True,
	)
	return response.output[1].content[0].text


def normalize_values(df: pd.DataFrame, method: str = 'zscore') -> pd.DataFrame:
	"""
	Normalize the 'value' column in df.

	method:
	    - "zscore": standard normalization
	    - "minmax": scale to [0, 1]
	    - "base": divide by first value

	Returns:
	    df with new 'value' column normalized.
	"""
	df = df.copy()
	if 'value' not in df.columns:
		raise ValueError("DataFrame must contain 'value' column")

	if method == 'zscore':
		mean = df['value'].mean()
		std = df['value'].std()
		df['value'] = (df['value'] - mean) / std
	elif method == 'minmax':
		min_val = df['value'].min()
		max_val = df['value'].max()
		df['value'] = (df['value'] - min_val) / (max_val - min_val)
	elif method == 'base':
		base_val = df['value'].iloc[0]
		df['value'] = df['value'] / base_val
	else:
		raise ValueError(f'Unknown normalization method: {method}')

	return df


def get_daily_active_addresses(
	slug: str, start_date: str, end_date: str
) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
	"""Fetch Telegram sentiment score from cache or API."""

	if api_key := os.environ.get('SANPY_APIKEY'):
		san.ApiConfig.api_key = api_key

	san_slug = f'daily_active_addresses/{slug}'
	df = san.get(san_slug, from_date=start_date, to_date=end_date, interval='4h')

	df_renamed = df.reset_index().rename(columns={'datetime': 'time'})
	daily_active_address = [
		SocialSentimentScoreValue(**{**row, 'time': row['time'].isoformat()})
		for row in df_renamed.to_dict(orient='records')
	]

	# _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
	return daily_active_address, df_renamed


def analyse_daa_trend(df: pd.DataFrame):
	"""
	Advanced analysis of DAA (Daily Active Addresses):
	- Short-term EMA-based trend classification.
	- MACD crossover momentum signal.
	- Additional slope metric for trend strength.

	Returns:
	    dict:
	        {
	            'trend': 'increasing' | 'decreasing' | 'stable',
	            'macd_signal': 'bullish' | 'bearish' | 'neutral',
	            'metrics': {
	                'ema_slope': float,
	                'macd_current': float,
	                'macd_signal_current': float,
	                'macd_hist_current': float
	            },
	            'explanation': str
	        }
	"""
	if df.empty or 'value' not in df.columns:
		return {
			'trend': 'unknown',
			'macd_signal': 'unknown',
			'metrics': {},
			'explanation': 'DAA data is empty or invalid.',
		}
	df = normalize_values(df, method='zscore')
	# Compute short-term EMA
	bars_2d = 3 * 6  # ~2 days for 8h bars
	df['ema_short'] = df['value'].ewm(span=bars_2d, adjust=False).mean()
	recent_ema = df['ema_short'].tail(bars_2d)

	# Compute slope of recent EMA for smoother trend signal
	x = np.arange(len(recent_ema))
	y = recent_ema.values
	slope, _, _, _, _ = linregress(x, y)
	ema_slope = float(slope)

	# Trend classification with slope + count logic
	inc_count = (recent_ema.diff() > 0).sum()
	dec_count = (recent_ema.diff() < 0).sum()

	if ema_slope > 0 and inc_count > bars_2d / 2:
		trend = 'increasing'
	elif ema_slope < 0 and dec_count > bars_2d / 2:
		trend = 'decreasing'
	else:
		trend = 'stable'

	# MACD computation
	ema_12 = df['value'].ewm(span=12, adjust=False).mean()
	ema_26 = df['value'].ewm(span=26, adjust=False).mean()
	macd = ema_12 - ema_26
	macd_sig = macd.ewm(span=9, adjust=False).mean()
	macd_hist = macd - macd_sig

	macd_now = macd.iloc[-1]
	sig_now = macd_sig.iloc[-1]
	hist_now = macd_hist.iloc[-1]
	macd_prev = macd.iloc[-2]
	sig_prev = macd_sig.iloc[-2]

	if macd_prev < sig_prev and macd_now > sig_now:
		macd_signal = 'bullish'
	elif macd_prev > sig_prev and macd_now < sig_now:
		macd_signal = 'bearish'
	else:
		macd_signal = 'neutral'

	return {
		'trend': trend,
		'macd_signal': macd_signal,
		'metrics': {
			'ema_slope': ema_slope,
			'macd_current': macd_now,
			'macd_signal_current': sig_now,
			'macd_hist_current': hist_now,
		},
	}


if __name__ == '__main__':
	# current_date = '2025-07-20'

	# whale_news = get_on_chain_openai('BTC', current_date)

	# print('Whale Activity News:\n', whale_news)

	llm = get_llm()

	agent = initialize_agent(
		tools=[],
		llm=llm,
		agent=AgentType.OPENAI_FUNCTIONS,
		verbose=True,
	)

	result = agent.run(
		'Use the get_daa_trend_analysis tool for bitcoin from 2024-02-10 to 2024-02-24.'
	)


# # use the below function to analyse only if you have real time subscription to the santiment data.
# # transaction_volume_in_profit one month delay
# def get_transaction_volume_in_profit(
# 	slug: str, start_date: str, end_date: str
# ) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
# 	"""Fetch Telegram sentiment score from cache or API."""
# 	# Check cache first
# 	# if cached_data := _cache.get_telegram_sentiment_score():
# 	#     return [SocialDominanceValue(**value) for value in cached_data]

# 	# If not in cache, fetch from API
# 	if api_key := os.environ.get('SANPY_APIKEY'):
# 		san.ApiConfig.api_key = api_key

# 	san_slug = f'transaction_volume_in_profit/{slug}'
# 	df = san.get(san_slug, from_date=start_date, to_date=end_date, interval='4h')

# 	df_renamed = df.reset_index().rename(columns={'datetime': 'time'})
# 	transaction_volume_in_profit = [
# 		SocialSentimentScoreValue(**{**row, 'time': row['time'].isoformat()})
# 		for row in df_renamed.to_dict(orient='records')
# 	]

# 	# _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
# 	return transaction_volume_in_profit, df_renamed


# # transaction_volume_profit_loss_ratio
# def get_transaction_volume_profit_loss_ratio(
# 	slug: str, start_date: str, end_date: str
# ) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
# 	"""Fetch Telegram sentiment score from cache or API."""
# 	# Check cache first
# 	# if cached_data := _cache.get_telegram_sentiment_score():
# 	#     return [SocialDominanceValue(**value) for value in cached_data]

# 	# If not in cache, fetch from API
# 	if api_key := os.environ.get('SANPY_APIKEY'):
# 		san.ApiConfig.api_key = api_key

# 	san_slug = f'transaction_volume_profit_loss_ratio/{slug}'
# 	df = san.get(san_slug, from_date=start_date, to_date=end_date, interval='4h')

# 	df_renamed = df.reset_index().rename(columns={'datetime': 'time'})
# 	transaction_volume_profit_loss_ratio = [
# 		SocialSentimentScoreValue(**{**row, 'time': row['time'].isoformat()})
# 		for row in df_renamed.to_dict(orient='records')
# 	]

# 	# _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
# 	return transaction_volume_profit_loss_ratio, df_renamed


# # 'transaction_volume_change_1d', 'transaction_volume_change_30d', 'transaction_volume_change_7d' can only get data from one month ago.
# def get_transaction_volume_change_1d(
# 	slug: str, start_date: str, end_date: str
# ) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
# 	"""Fetch Telegram sentiment score from cache or API."""
# 	# Check cache first
# 	# if cached_data := _cache.get_telegram_sentiment_score():
# 	#     return [SocialDominanceValue(**value) for value in cached_data]

# 	# If not in cache, fetch from API
# 	if api_key := os.environ.get('SANPY_APIKEY'):
# 		san.ApiConfig.api_key = api_key

# 	san_slug = f'transaction_volume_change_1d/{slug}'
# 	df = san.get(san_slug, from_date=start_date, to_date=end_date, interval='4h')

# 	df_renamed = df.reset_index().rename(columns={'datetime': 'time'})
# 	transaction_volume_change_1d = [
# 		SocialSentimentScoreValue(**{**row, 'time': row['time'].isoformat()})
# 		for row in df_renamed.to_dict(orient='records')
# 	]

# 	# _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
# 	return transaction_volume_change_1d, df_renamed


# # "whale_transaction_count_100k_usd_to_inf_change_1d'"
# # with one month delay
# def get_whale_transaction_count_100k_usd_to_inf_change_1d(
# 	slug: str, start_date: str, end_date: str
# ) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
# 	"""Fetch Telegram sentiment score from cache or API."""
# 	# Check cache first
# 	# if cached_data := _cache.get_telegram_sentiment_score():
# 	#     return [SocialDominanceValue(**value) for value in cached_data]

# 	# If not in cache, fetch from API
# 	if api_key := os.environ.get('SANPY_APIKEY'):
# 		san.ApiConfig.api_key = api_key

# 	san_slug = f'whale_transaction_count_100k_usd_to_inf_change_1d/{slug}'
# 	df = san.get(san_slug, from_date=start_date, to_date=end_date, interval='4h')

# 	df_renamed = df.reset_index().rename(columns={'datetime': 'time'})
# 	whale_transaction_count_100k_usd_to_inf_change_1d = [
# 		SocialSentimentScoreValue(**{**row, 'time': row['time'].isoformat()})
# 		for row in df_renamed.to_dict(orient='records')
# 	]

# 	# _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
# 	return whale_transaction_count_100k_usd_to_inf_change_1d, df_renamed


# if __name__ == '__main__':
# 	# Example usage
# 	slug = 'bitcoin'
# 	start_date = '2025-06-07'
# 	end_date = '2025-07-26'

# 	# can only get the data one month ago. transaction_volume_change_1d
# 	_, transaction_volume_in_profit = get_transaction_volume_in_profit(
# 		slug, start_date, end_date
# 	)
# 	# print(daily_active_addresses)
# 	# result = analyse_data_trend(daily_active_addresses)
# 	print(transaction_volume_in_profit)
