import os
import pandas as pd
from typing import Tuple
from base_workflow.data.cache import get_cache
from base_workflow.data.models import (
	SocialSentimentScoreValue,
)

# Global cache instance
_cache = get_cache()

import san


def get_daily_active_addresses(
	slug: str, start_date: str, end_date: str
) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
	"""Fetch Telegram sentiment score from cache or API."""
	# Check cache first
	# if cached_data := _cache.get_telegram_sentiment_score():
	#     return [SocialDominanceValue(**value) for value in cached_data]

	# If not in cache, fetch from API
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


if __name__ == '__main__':
	# Example usage
	slug = 'bitcoin'
	start_date = '2024-06-07'
	end_date = '2024-06-21'

	_, daily_active_addresses = get_daily_active_addresses(slug, start_date, end_date)
	# print(daily_active_addresses)
	result = analyse_data_trend(daily_active_addresses)
	print(result)
