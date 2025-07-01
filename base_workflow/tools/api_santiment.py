from ast import Str
import os
from unittest import skip
from duckduckgo_search.cli import news
from fontTools.misc.plistlib import _date_parser
from humanfriendly.text import compact
import pandas as pd
from pydantic import datetime_parse
import requests
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Optional
from io import StringIO

from test.test_threading_local import target


from base_workflow.data.cache import get_cache
from base_workflow.data.models import (
    CompanyNews,
    CompanyNewsResponse,
    SocialDominanceValue,
    SocialDominanceResponse,
    SocialSentimentScoreResponse,
    SocialSentimentScoreValue,
    SocialVolumeValue,
    SocialVolumeResponse,
    SocialVolumeChange,
    SocialVolumeChangeResponse,
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)
import requests
from base_workflow.data.models import FearGreedIndex
from datetime import datetime, timezone


# Global cache instance
_cache = get_cache()

import san
import pandas as pd

# Sentiment Analysis
# Calculate a weighted sentiment score (sentiment_score) by aggregating sentiment data from Telegram, Twitter and Reddit
# Social Volume analysis
# combine the discussion volume (volume_score) from Telegram, Twitter, and YouTube. A higher discussion volume typically 
# indicates increased market interest in an asset, which could be a precursor to price fluctuations
def get_sentiment_weighted_total(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_weighted_total/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    sentiment_weighted_total = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return sentiment_weighted_total

def get_social_volume_total(slug: str, start_date: str, end_date: str) -> list[SocialVolumeValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "social_volume_total/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    social_volume_total = [
        SocialVolumeValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return social_volume_total

def get_social_volume_total_change_30d(slug: str, start_date: str, end_date: str) -> list[SocialVolumeChange]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "social_volume_total_change_30d/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    social_volume_total_change_30d = [
        SocialVolumeChange(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return social_volume_total_change_30d

def get_social_volume_total_change_7d(slug: str, start_date: str, end_date: str) -> list[SocialVolumeChange]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "social_volume_total_change_7d/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    social_volume_total_change_7d = [
        SocialVolumeChange(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return social_volume_total_change_7d

def get_social_volume_total_change_1d(slug: str, start_date: str, end_date: str) -> list[SocialVolumeChange]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "social_volume_total_change_1d/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    social_volume_total_change_1d = [
        SocialVolumeChange(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return social_volume_total_change_1d

def get_sentiment_negative_total(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Shows how many mentions of a term/asset are expressed in a negative manner"""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_negative_total/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    sentiment_negative_total = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return sentiment_negative_total

def get_sentiment_positive_total(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Shows how many mentions of a term/asset are expressed in a positive manner"""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_positive_total/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    sentiment_positive_total = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return sentiment_positive_total

def get_sentiment_balance_total(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Sentiment Balance - The difference between Positive Sentiment and Negative Sentiment"""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_balance_total/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    sentiment_balance_total = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return sentiment_balance_total

# check how to get data of responded date
def get_fear_and_greed_index(target_date: Optional[str] = None) -> FearGreedIndex:
    """
    Fetch the Fear and Greed Index from the Alternative.me API.
    
    Returns:
        FearGreedIndex: A structured object containing the index value, classification.
    """
    try:
        # If target_date is provided, format it to the required date format
        if target_date:
            response = requests.get("https://api.alternative.me/fng/?limit=0&date_format=cn")
            fng = response.json()
            df = pd.DataFrame(fng["data"])
            index_data = df[df["timestamp"] == target_date]
            index_value = str(index_data["value"].iloc[0])
            classification = str(index_data["value_classification"].iloc[0])
            updated_at = target_date
        else:
            response = requests.get("https://api.alternative.me/fng/?limit=1&date_format=cn")
            data = response.json()           
            index_data = data["data"][0]
            index_value = str(index_data["value"])
            classification = index_data["value_classification"]
            updated_at = index_data["timestamp"]
            # dt = datetime.strptime(timestamp, "%d-%m-%Y").replace(tzinfo=timezone.utc)
            # updated_at = dt.strftime("%Y-%m-%d")

   
        result = FearGreedIndex(
            value=index_value,
            classification=classification,
            updated_at=updated_at
        )
        return result


    except requests.RequestException as e:
        print(f"Error fetching Fear and Greed Index: {e}")
        return FearGreedIndex(value=0, classification="neutral", updated_at="Unknown") # set to neutral if error occurs
    
if __name__ == "__main__":
    # Example usage
    fgi_1 = get_fear_and_greed_index("2025-07-01")
    print(f"Fear and Greed Index: {fgi_1.value}, Classification: {fgi_1.classification}, Updated at: {fgi_1.updated_at}")
    fgi_2 = get_fear_and_greed_index()
    print(f"Fear and Greed Index: {fgi_2.value}, Classification: {fgi_2.classification}, Updated at: {fgi_2.updated_at}")

