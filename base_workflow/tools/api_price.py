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
    prices = get_prices(slug, start_date, end_date, "4h")
    return prices_to_df(prices)

if __name__ == "__main__":
    # Example usage
    slug = "ohlcv/bitcoin"       
    start_date="2024-06-07"
    end_date="2025-05-08"
    # # end_date = datetime.utcnow().date().isoformat()
    # end_date = "2025-05-08"
    # end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    # start_dt = end_dt - timedelta(weeks=2)
    # start_date = start_dt.date().isoformat()
    
    prices_df = get_price_data(slug, start_date, end_date)
    print(prices_df.head())