import os
from duckduckgo_search.cli import news
from humanfriendly.text import compact
import pandas as pd
import requests
import pandas as pd
from datetime import datetime, timedelta

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


def get_fear_and_greed_index() -> FearGreedIndex:
    """
    Fetch the Fear and Greed Index from the Alternative.me API.
    
    Returns:
        FearGreedIndex: A structured object containing the index value, classification, and last updated time.
    """
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        
        index_data = data["data"][0]

        index_value = int(index_data["value"])
        classification = index_data["value_classification"]
        timestamp = int(index_data["timestamp"])

       
        updated_at = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
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
    fgi = get_fear_and_greed_index()
    print(f"Fear and Greed Index: {fgi.value}, Classification: {fgi.classification}, Updated at: {fgi.updated_at}")

    # # test get_prices
    # slug = "social_volume_total_change_30d/bitcoin"       
    # # start_date="2024-06-07"
    # # end_date="2025-05-08"
    # # end_date = datetime.utcnow().date().isoformat()
    # end_date = "2025-05-08"
    # end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    # start_dt = end_dt - timedelta(weeks=2)
    # start_date = start_dt.date().isoformat()

    # social_volume_total_change_7d = get_social_volume_total_change_1d(
    #     slug,
    #     end_date=end_date,
    #     start_date=start_date,
    # )
    # print(social_volume_total_change_7d)