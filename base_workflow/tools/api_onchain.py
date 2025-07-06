import os
import pandas as pd
import pandas as pd
from typing import Tuple
from base_workflow.data.cache import get_cache
from base_workflow.data.models import (
    SocialSentimentScoreValue,
)

# Global cache instance
_cache = get_cache()

import san
import pandas as pd

def get_sentiment_weighted_total(slug: str, start_date: str, end_date: str) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    df = san.get(
        "sentiment_weighted_total/bitcoin", 
        from_date=start_date, 
        to_date=end_date, 
        interval="4h" 
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    sentiment_weighted_total = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return sentiment_weighted_total, df_renamed
