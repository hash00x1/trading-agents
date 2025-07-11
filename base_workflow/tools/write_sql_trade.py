from typing import Annotated
from langchain_core.tools import tool
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("base_workflow/outputs/trades.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    action TEXT CHECK(action IN ('buy', 'sell', 'hold')) NOT NULL,
    symbol TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0)
);
"""

# Init database
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()

init_db()

print("Database initialized at", DB_PATH.resolve())

# # @tool
# def write_sql_trade(
#     action: Annotated[str, "buy/sell/hold"],
#     symbol: Annotated[str, "e.g. 'ETH'"],
#     amount: Annotated[float, "Quantity traded, hold is '0'."]
# ) -> Annotated[str, "Confirmation message after writing the trade to the database."]:
#     ts = datetime.now(timezone.utc).isoformat()
#     with sqlite3.connect(DB_PATH) as conn:
#         conn.execute(
#             "INSERT INTO trades (timestamp, action, symbol, amount) VALUES (?, ?, ?, ?)",
#             (ts, action.lower(), symbol.upper(), amount)
#         )
#         conn.commit()
#     return f"Recorded: {action.upper()} {amount} {symbol.upper()} at {ts}"



# if __name__ == "__main__":
#     result1 = write_sql_trade(action="buy", symbol="BTC", amount=0.5)
#     print(result1)

#     result2 = write_sql_trade(action="sell", symbol="ETH", amount=1.2)
#     print(result2)

#     result3 = write_sql_trade(action="hold", symbol="ADA", amount=0.0)
#     print(result3)