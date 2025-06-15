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

def get_prices(slug: str, start_date: str, end_date: str, time_interval: str) -> list[Price]:
    """Fetch price data from cache or API."""
    # Check cache first
    if cached_data := _cache.get_prices(slug):
        # Filter cached data by date range and convert to Price objects
        filtered_data = [Price(**price) for price in cached_data if start_date <= price["time"] <= end_date]
        if filtered_data:
            return filtered_data

    # If not in cache or no data in range, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
                slug,
                from_date = start_date,
                to_date=end_date,
                interval=time_interval
                ) 
    df_renamed = df.rename(columns={
                "openPriceUsd": "open",
                "closePriceUsd": "close",
                "highPriceUsd": "high",
                "lowPriceUsd": "low",
                "volume": "volume"
                })
    df_renamed = df_renamed.reset_index().rename(columns={"datetime": "time"})
    prices = [
        Price(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    _cache.set_prices(slug, [p.model_dump() for p in prices])
    return prices

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

if __name__ == "__main__":
    # test get_prices
    slug = "sentiment_negative_youtube_videos/bitcoin"       
    # start_date="2024-06-07"
    # end_date="2025-05-08"
    # end_date = datetime.utcnow().date().isoformat()
    end_date = "2025-05-08"
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(weeks=2)
    start_date = start_dt.date().isoformat()

    telegram_negative_sentiment_score = get_telegram_negative_sentiment_score(
        slug,
        end_date=end_date,
        start_date=start_date,
    )
    print(telegram_negative_sentiment_score)



# def search_line_items(
#     ticker: str,
#     line_items: list[str],
#     end_date: str,
#     period: str = "ttm",
#     limit: int = 10,
# ) -> list[LineItem]:
#     """Fetch line items from API."""
#     # If not in cache or insufficient data, fetch from API
#     headers = {}
#     if api_key := os.environ.get("FINANCIAL_DATASETS_API_KEY"):
#         headers["X-API-KEY"] = api_key

#     url = "https://api.financialdatasets.ai/financials/search/line-items"

#     body = {
#         "tickers": [ticker],
#         "line_items": line_items,
#         "end_date": end_date,
#         "period": period,
#         "limit": limit,
#     }
#     response = requests.post(url, headers=headers, json=body)
#     if response.status_code != 200:
#         raise Exception(f"Error fetching data: {ticker} - {response.status_code} - {response.text}")
#     data = response.json()
#     response_model = LineItemResponse(**data)
#     search_results = response_model.search_results
#     if not search_results:
#         return []

#     # Cache the results
#     return search_results[:limit]


# get on-chain metrics like active addresses, transaction volume, whale behavior
# def get_onchain_metrics() 

def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert prices to a DataFrame."""
    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


# Update the get_price_data function to use the new functions
def get_price_data(slug: str, start_date: str, end_date: str) -> pd.DataFrame:
    prices = get_prices(slug, start_date, end_date, "1d")
    return prices_to_df(prices)