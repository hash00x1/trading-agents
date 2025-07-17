from langchain_core.tools import tool
import sqlite3
from datetime import datetime
from pathlib import Path
from langchain_openai import ChatOpenAI


@tool
def buy(symbol: str, quantity: float, price: float) -> str:
	"""
	Execute a BUY order by inserting into the trades table.
	"""
	db_path = Path('base_workflow/outputs/crypto_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute(
		"""
        CREATE TABLE IF NOT EXISTS trades (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          timestamp TEXT, action TEXT, symbol TEXT, amount REAL, price REAL
        )
        """
	)
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, symbol, amount, price) VALUES (?, 'buy', ?, ?, ?)",
		(timestamp, symbol, quantity, price),
	)
	conn.commit()
	conn.close()
	return f'Executed BUY for {symbol} | {quantity} @ {price}'


@tool
def sell(symbol: str, quantity: float, price: float) -> str:
	"""
	Execute a SELL order by inserting into the trades table.
	"""
	db_path = Path('base_workflow/outputs/crypto_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	cursor.execute(
		"""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, action TEXT, symbol TEXT, amount REAL, price REAL
        )
        """
	)
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, symbol, amount, price) VALUES (?, 'sell', ?, ?, ?)",
		(timestamp, symbol, quantity, price),
	)
	conn.commit()
	conn.close()
	return f'Executed SELL for {symbol} | {quantity} @ {price}'


@tool
def hold(symbol: str) -> str:
	"""
	No trade executed. Hold position.
	"""
	return f'HOLD: No trade executed for {symbol}. Position unchanged.'


TOOLS = [buy, sell, hold]

llm = ChatOpenAI(temperature=0)
llm_with_tools = llm.bind_tools(TOOLS)


# —— Tool Node 调度函数 ——
def hedging_tool_node(user_input: str) -> str:
	ai_msg = llm_with_tools.invoke(user_input)
	calls = (
		ai_msg.tool_calls
	)  # List[{"name","args",...}] :contentReference[oaicite:6]{index=6}
	if not calls:
		return ai_msg.content

	# 仅调用第一个工具（一次执行）
	call = calls[0]
	fn = next(t for t in TOOLS if t.name == call['name'])
	return fn.invoke(call['args'])


if __name__ == '__main__':
	for cmd in ['Buy 0.2 BTC at 29000', 'Sell 1 ETH at 1850', 'Hold DOGE']:
		print(f'\n> {cmd}')
		output = hedging_tool_node(cmd)
		print(output)
