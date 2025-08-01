from langchain_core.tools import tool
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd


# reading in tool.
#  crypto_trades change to slug_trade. Different tables for different slugs.
def read_trades(slug: str) -> pd.DataFrame:
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')

	if not db_path.exists():
		raise FileNotFoundError(
			f'Database not found at {db_path}. Please ensure trades have been recorded first.'
		)

	conn = sqlite3.connect(db_path)
	table_name = 'trades'

	# Find the latest timestamp
	latest_query = f'SELECT MAX(timestamp) FROM {table_name}'
	latest_timestamp = conn.execute(latest_query).fetchone()[0]

	# Get only trades with the latest timestamp
	query = f"""
        SELECT * FROM {table_name}
        WHERE timestamp = ?
    """
	df = pd.read_sql_query(query, conn, params=(latest_timestamp,))
	conn.close()
	return df


@tool
def buy(slug: str, amount: float, price: float, remaining_dollar: float) -> str:
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
          timestamp TEXT, action TEXT, slug TEXT, amount REAL, price REAL, remaining_dollar REAL
        )
        """
	)
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_dollar) VALUES (?, 'buy', ?, ?, ?, ?)",
		(timestamp, slug, amount, price, remaining_dollar),
	)
	conn.commit()
	conn.close()
	return f'Executed BUY for {slug} | {amount} @ {price}'


@tool
def sell(slug: str, amount: float, price: float, remaining_dollar: float) -> str:
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
            timestamp TEXT, action TEXT, slug TEXT, amount REAL, price REAL, remaining_dollar REAL
        )
        """
	)
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_dollar) VALUES (?, 'sell', ?, ?, ?, ?)",
		(timestamp, slug, amount, price, remaining_dollar),
	)
	conn.commit()
	conn.close()
	return f'Executed SELL for {slug} | {amount} @ {price}'


@tool
def hold(slug: str) -> str:
	"""
	No trade executed. Hold position.
	"""
	return f'HOLD: No trade executed for {slug}. Position unchanged.'


if __name__ == '__main__':
	# define hedging tool node
	# TOOLS = [buy, sell, hold]

	# llm = ChatOpenAI(temperature=0)
	# llm_with_tools = llm.bind_tools(TOOLS)

	# def hedging_tool_node(user_input: str) -> str:
	# 	# LLM generates an instruction indicating which tool it wants to call and with what parameters
	# 	ai_msg = llm_with_tools.invoke(user_input)
	# 	calls = ai_msg.tool_calls
	# 	if not calls:
	# 		return ai_msg.content

	# 	# assumed only one tool is used, based on the logic now
	# 	call = calls[0]
	# 	fn = next(t for t in TOOLS if t.name == call['name'])
	# 	return fn.invoke(call['args'])

	# for cmd in [
	# 	'Buy 0.2 BTC at 29000, remains are 1 BTC',  # unify all the writing style in portfolio_manager at outputs
	# 	'Sell 1 ETH at 1850, remains are 1345000 dollar',
	# 	'Hold DOGE',
	# ]:
	# 	# only one command would be given in one round.
	# 	print(f'\n> {cmd}')
	# 	output = hedging_tool_node(cmd)
	# 	print(output)

	test_slug = 'bitcoin'
	df = read_trades(test_slug)
	print(
		f"[INFO] Retrieved {len(df)} trades for slug '{test_slug}' at latest timestamp:"
	)
	print(df)
