import san
data = san.get("daily_active_addresses",
    slug="bitcoin",
    from_date="2024-01-01",
    to_date="2024-01-31",
    interval="1d")

print(data)