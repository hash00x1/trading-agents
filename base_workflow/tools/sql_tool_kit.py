from langchain_core.tools import tool
import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
from base_workflow.graph.state import AgentState
from langgraph.graph import StateGraph
from base_workflow.utils.llm_config import get_llm


#  reading in tool.
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
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	# cursor.execute(
	# 	"""
	#     CREATE TABLE IF NOT EXISTS trades (
	#       id INTEGER PRIMARY KEY AUTOINCREMENT,
	#       timestamp TEXT, action TEXT, slug TEXT, amount REAL, price REAL, remaining_dollar REAL
	#     )
	#     """
	# )
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
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	# cursor.execute(
	# 	"""
	#     CREATE TABLE IF NOT EXISTS trades (
	#         id INTEGER PRIMARY KEY AUTOINCREMENT,
	#         timestamp TEXT, action TEXT, slug TEXT, amount REAL, price REAL, remaining_dollar REAL
	#     )
	#     """
	# )
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
	# define hedging tool node
	TOOLS = [buy, sell, hold]

	# llm = ChatOpenAI(temperature=0)
	llm = get_llm()
	llm_with_tools = llm.bind_tools(TOOLS)

	def hedging_tool_node(state: AgentState) -> dict:
		input = state.get('data', {}).get('Portfolio manager', '')

		if not isinstance(input, str) or not input.strip():
			return {'error': "Missing or invalid 'Portfolio manager' input."}

		try:
			ai_msg = llm_with_tools.invoke(input)
		except Exception as e:
			return {'error': f'LLM invocation failed: {str(e)}'}

		calls = ai_msg.tool_calls
		if not calls:
			return {'result': ai_msg.content}

		call = calls[0]
		fn = next((t for t in TOOLS if t.name == call['name']), None)
		if not fn:
			return {'error': f"Tool '{call['name']}' not found."}

		try:
			tool_result = fn.invoke(call['args'])
		except Exception as e:
			return {'error': f'Tool execution failed: {str(e)}'}

		return {
			'tool_name': call['name'],
			'tool_args': call['args'],
			'tool_result': tool_result,
		}

	workflow = StateGraph(AgentState)
	workflow.add_node('hedging_tool', hedging_tool_node)
	workflow.set_entry_point('hedging_tool')
	graph = workflow.compile()

	state = {
		'data': {'Portfolio manager': 'Final Decision: **Buy** | 9,500,000.000000 PEPE'}
	}

	final_state = graph.invoke(state)
	print(final_state)

	# Portfolio manager has already decide the output
	# for cmd in [
	# 	'Final Decision: **Buy** | 8.741571 BTC',
	# 	'Final Decision: **Sell** | 3.208194 ETH',
	# 	'Final Decision: **Buy** | 9,500,000.000000 PEPE'
	# ]:

	# for cmd in [
	# 	'Buy 0.2 BTC at 29000, remains are 1 BTC',  # unify all the writing style in portfolio_manager at outputs
	# 	'Sell 1 ETH at 1850, remains are 1345000 dollar',
	# 	'Hold DOGE',
	# ]:
	# 	# only one command would be given in one round.
	# 	print(f'\n> {cmd}')
	# 	output = hedging_tool_node(cmd)
	# 	print(output)
