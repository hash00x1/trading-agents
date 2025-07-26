import san

san.ApiConfig.api_key = 'rkf5d3lrsulqpyl3_47npxf6doa5fi4ok'

# available metrics in santiment
metrics = san.available_metrics()
print(metrics)
# Fetch OHLCV data
# data = san.get(
# 	'ohlcv/bitcoin',  # <-- replace 'bitcoin' with your asset slug, e.g. 'ethereum', 'aave', etc.
# 	# Slug="bitcoin",
# 	from_date='2025-07-01T00:00:00+00:00',
# 	to_date='2025-07-20T23:59:59+00:00',
# 	interval='1d',
# )
# Adjusted date range within the allowed interval
# data_1 = san.get(
# 	'active_addresses_30d/bitcoin',  # Replace 'bitcoin' with your asset slug
# 	from_date='2025-07-07',  # Start date within allowed range
# 	to_date='2025-07-20',  # End date within allowed range
# 	# interval="1d"  # Set the interval to daily data
# )
# data_2 = san.get(
#     "daily_active_addresses/bitcoin",  # Replace 'bitcoin' with your asset slug
#     from_date="2025-05-08T00:00:00Z",  # Start date within allowed range
#     to_date="2025-05-08T00:00:00Z",  # End date within allowed range
#     #interval="1d"  # Set the interval to daily data
# )

# Display result
# print(data_1)
# print(data)
