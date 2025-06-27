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
    FinancialMetrics,
    FinancialMetricsResponse,
    Price,
    PriceResponse,
    LineItem,
    LineItemResponse,
    InsiderTrade,
    InsiderTradeResponse,
)

# Global cache instance
_cache = get_cache()

import san
import pandas as pd

# Sentiment Analysis
# Calculate a weighted sentiment score (sentiment_score) by aggregating sentiment data from Telegram, Twitter and Reddit
# Social Volume analysis
# combine the discussion volume (volume_score) from Telegram, Twitter, and YouTube. A higher discussion volume typically 
# indicates increased market interest in an asset, which could be a precursor to price fluctuations
def get_telegram_positive_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_positive_telegram/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    telegram_positive_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return telegram_positive_sentiment_score

def get_telegram_negative_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_negative_telegram/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    telegram_negative_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return telegram_negative_sentiment_score

def get_reddit_positive_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_positive_reddit/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    reddit_positive_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return reddit_positive_sentiment_score


def get_reddit_negative_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_negative_reddit/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    reddit_negative_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return reddit_negative_sentiment_score

def get_twitter_positive_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_positive_twitter/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    twitter_positive_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return twitter_positive_sentiment_score

def get_twitter_negative_sentiment_score(slug: str, start_date: str, end_date: str) -> list[SocialSentimentScoreValue]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_negative_twitter/bitcoin",  # Replace 'bitcoin' with your asset slug
        from_date=start_date,  # Start date within allowed range
        to_date=end_date,  # End date within allowed range
        #interval="1d"  # Set the interval to daily data
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    twitter_negative_sentiment_score = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return twitter_negative_sentiment_score

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


if __name__ == "__main__":
    # test get_prices
    slug = "sentiment_balance_total/bitcoin"       
    # start_date="2024-06-07"
    # end_date="2025-05-08"
    # end_date = datetime.utcnow().date().isoformat()
    end_date = "2025-05-08"
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(weeks=2)
    start_date = start_dt.date().isoformat()

    sentiment_balance_total = get_sentiment_balance_total(
        slug,
        end_date=end_date,
        start_date=start_date,
    )
    print(sentiment_balance_total)