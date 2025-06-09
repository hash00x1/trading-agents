from pygments.lexers.shell import SlurmBashLexer
import san
import san
san.ApiConfig.api_key = "rkf5d3lrsulqpyl3_47npxf6doa5fi4ok"

# available metrics in santiment
# metrics = san.available_metrics()
# print(metrics)
# Fetch OHLCV data
# data = san.get(
#     "social_dominance_telegram/bitcoin",        # <-- replace 'bitcoin' with your asset slug, e.g. 'ethereum', 'aave', etc.
#     # Slug="bitcoin", 
#     from_date="2024-01-01T00:00:00+00:00",
#     to_date="2024-01-10T23:59:59+00:00",
#     interval="1d"
# )
# Adjusted date range within the allowed interval
data_1 = san.get(
    "sentiment_positive_reddit/bitcoin",  # Replace 'bitcoin' with your asset slug
    from_date="2024-06-07",  # Start date within allowed range
    to_date="2025-05-08",  # End date within allowed range
    #interval="1d"  # Set the interval to daily data
)
data_2 = san.get(
    "sentiment_negative_reddit/bitcoin",  # Replace 'bitcoin' with your asset slug
    from_date="2024-06-07",  # Start date within allowed range
    to_date="2025-05-08",  # End date within allowed range
    #interval="1d"  # Set the interval to daily data
)

# Display result
print(data_1)
print(data_2)

