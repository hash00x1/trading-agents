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

def get_daily_active_addresses(slug: str, start_date: str, end_date: str) -> Tuple[list[SocialSentimentScoreValue], pd.DataFrame]:
    """Fetch Telegram sentiment score from cache or API."""
    # Check cache first
    # if cached_data := _cache.get_telegram_sentiment_score():
    #     return [SocialDominanceValue(**value) for value in cached_data]

    # If not in cache, fetch from API
    if api_key := os.environ.get("SANPY_APIKEY"):
        san.ApiConfig.api_key = api_key

    san_slug = f"daily_active_addresses/{slug}"
    df = san.get(
        san_slug, 
        from_date=start_date, 
        to_date=end_date, 
        interval="4h" 
    )

    df_renamed = df.reset_index().rename(columns={"datetime": "time"})
    daily_active_address = [
        SocialSentimentScoreValue(**{**row, "time": row["time"].isoformat()})
        for row in df_renamed.to_dict(orient="records")
    ]
    
    # _cache.set_telegram_sentiment_score([v.model_dump() for v in dominance_values])
    return daily_active_address, df_renamed

# # 7d moving average. 
# def analyse_daa_trend(df: pd.DataFrame):
#     """
#     Analyze DAA (Daily Active Addresses) data using EMA and MACD to assess short-term activity trend and momentum.

#     Args:
#         df (pd.DataFrame): DataFrame with 'value' column representing DAA values.

#     Returns:
#         dict: {
#             'daa_trend': str,
#                 'increasing', 'decreasing', or 'stable' (majority of recent EMA bars)
#             'macd_signal': str,
#                 'bullish', 'bearish', or 'neutral' (MACD crossover)
#         }
#     """
#     bars_2d = 3 * 6  # roughly 2 days assuming 8h bars (or adjust as needed)
#     df['ema_3'] = df['value'].ewm(span=bars_2d).mean()
#     recent = df['ema_3'].tail(bars_2d)

#     increasing_count = (recent.diff() > 0).sum()
#     decreasing_count = (recent.diff() < 0).sum()

#     if increasing_count > bars_2d / 2:
#         trend = "increasing"
#     elif decreasing_count > bars_2d / 2:
#         trend = "decreasing"
#     else:
#         trend = "stable"

#     ema_12 = df['value'].ewm(span=12, adjust=False).mean()
#     ema_26 = df['value'].ewm(span=26, adjust=False).mean()
#     macd = ema_12 - ema_26
#     signal = macd.ewm(span=9, adjust=False).mean()

#     last = pd.DataFrame({'macd': macd, 'signal': signal}).iloc[-2:]
#     macd_prev, sig_prev = last['macd'].iloc[0], last['signal'].iloc[0]
#     macd_now, sig_now = last['macd'].iloc[1], last['signal'].iloc[1]

#     if macd_prev < sig_prev and macd_now > sig_now:
#         macd_signal = 'bullish'
#     elif macd_prev > sig_prev and macd_now < sig_now:
#         macd_signal = 'bearish'
#     else:
#         macd_signal = 'neutral'

#     return {"daa_trend": trend, "macd_signal": macd_signal}
import pandas as pd
import numpy as np
from scipy.stats import linregress

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
            "trend": "unknown",
            "macd_signal": "unknown",
            "metrics": {},
            "explanation": "DAA data is empty or invalid."
        }

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
        trend = "increasing"
    elif ema_slope < 0 and dec_count > bars_2d / 2:
        trend = "decreasing"
    else:
        trend = "stable"

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

    # Build explanation for agent consumption
    explanation = (
        f"DAA short-term EMA slope: {ema_slope:.4f}. "
        f"Recent trend classified as {trend}. "
        f"MACD: {macd_now:.2f}, Signal: {sig_now:.2f}, Hist: {hist_now:.2f}. "
        f"MACD signal interpreted as {macd_signal}."
    )

    return {
        "trend": trend,
        "macd_signal": macd_signal,
        "metrics": {
            "ema_slope": ema_slope,
            "macd_current": macd_now,
            "macd_signal_current": sig_now,
            "macd_hist_current": hist_now
        },
        "explanation": explanation
    }


if __name__ == "__main__":
    # Example usage
    slug = "bitcoin"       
    start_date="2024-06-07"
    end_date="2024-06-21"
    
    _, daily_active_addresses = get_daily_active_addresses(slug, start_date, end_date)
    #print(daily_active_addresses)
    result = analyse_daa_trend(daily_active_addresses)
    print(result)
