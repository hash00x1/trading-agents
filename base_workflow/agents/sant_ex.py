import san
import pandas as pd

result_1  = san.get(
    "ohlcv/santiment",
    from_date="2018-06-01",
    to_date="2018-06-05",
    interval="1d"
)
result_2 = san.get(
    "price_usd",
    slug="bitcoin",
    from_date="2024-05-01",
    to_date="2024-05-20",
    interval="1d"
)
print(result_1)
print(result_2)