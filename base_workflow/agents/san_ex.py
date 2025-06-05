import san
import san
san.ApiConfig.api_key = "rkf5d3lrsulqpyl3_47npxf6doa5fi4ok"


# metrics = san.available_metrics()
# print(metrics)
# Fetch OHLCV data
data = san.get(
    "ohlcv/bitcoin",        # <-- replace 'bitcoin' with your asset slug, e.g. 'ethereum', 'aave', etc.
    from_date="2023-01-01",
    to_date="2023-01-10",
    interval="1d"
)

# Display result
print(data)

