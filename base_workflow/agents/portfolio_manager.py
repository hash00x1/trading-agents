import json
from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from base_workflow.tools import get_real_time_price
from datetime import datetime
import sqlite3
from pathlib import Path
import re
from base_workflow.utils.llm_config import get_llm

# You have access to the following tools:
# Calculate_Amount: "Description"
# Buy: ""
# Sell: ""
# Hold: "" -> defined as return None
# def Hold:
#     return None
# 'dollar balance': dollar_balance,
# 'token balance': token_balance,


def portfolio_manager(state: AgentState):
	messages = state.get('messages', [])
	data = state.get('data', {})  # maybe also get price
	slug = str(data.get('slug'))
	token = str(data.get('token'))
	dollar_balance = data.get('dollar balance', 0)
	token_balance = data.get('token balance', 0)
	llm = get_llm()

	progress.update_status(
		'portfolio_manager', slug, 'Aggregating multi-agent signals and deciding.'
	)
	portfolio_analysis = {}

	try:  # if not get the newest price use the latest ohlcv price instead.
		crypto_price = get_real_time_price(token)
	except Exception:
		crypto_price = state['data']['close_price']

	# print(crypto_price)
	# print(dollar_balance)
	analyst_summary_prompt = f"""
	You are a crypto portfolio manager in a multi-agent system.
	You need to behave like a dictator.
	You must consider all analyst inputs (technical, sentiment, on-chain, risk, research, and news), and determine whether there is a **dominant trend or shared conviction** among them.
	For the asset **{slug}**, you have received signal reports from different analysts (technical, sentiment, on-chain, research, risk, news, etc.).
	Your task is to **evaluate all analyst inputs equally**, identify whether a clear directional trend or consensus exists, and make a trading decision accordingly.
	You currently have **{dollar_balance}** in your wallet, the correct token balance is **{token_balance}**.
	the current market price of **{slug}** is **{crypto_price}**.

	You need to: 
	- Determine the Market Environment:
		- **Favorable to Buy** → if most strong signals or leading indicators support upside potential.
		- **Favorable to Sell** → if dominant indicators or risks suggest downside exposure.
		- **Neutral**: Try to avoid, only select if:
			- The technical signal is itself Neutral, **and**
			- No more than one other analyst gives a strong directional signal.
			- Or all analysts are explicitly contradictory and cancel each other.

	- Return the final decision using this **exact format** (no explanation or extra text):	
	- `Final Decision: **Buy** `
	- `Final Decision: **Sell** `
	- `Final Decision: **Hold**`
	Please keep the format consistent and clean. Do not include any additional output.

	""".format(
		slug=slug,
		dollar_balance=dollar_balance,
		token_balance=token_balance,
		crypto_price=crypto_price,
	)
	portfolio_decision_agent = create_react_agent(
		llm,
		tools=[],
		state_modifier=analyst_summary_prompt,
	)

	response = portfolio_decision_agent.invoke({'messages': messages})
	content = response['messages'][-1].content
	match_signal = re.search(r'Final Decision: \*\*(Buy|Hold|Sell)\*\*', content)
	if match_signal:
		decision = match_signal.group(1)  # Extracts 'Buy', 'Sell', or 'Hold'
	else:
		decision = None
	# ### Step 2: Choose a Trading Action Based on Environment and Holdings
	# Follow this rule:
	# - If the environment is **favorable to buy**:
	# 	- If `dollar_balance > 0`, then:
	# 		- Call `calculate_buy_quantity(dollar_balance, crypto_price)` to get how many tokens can be bought.
	# 		- Return: `Final Decision: **Buy**` | [calculated token quantity]
	# 	- If `dollar_balance == 0`, then: `Final Decision: **Hold**`.
	# - If the environment is **favorable to sell**:
	# 	- If `token_balance > 0`, then:
	# 		- Call `calculate_sell_value(token_balance, crypto_price)` to get how much USD can be received.
	# 		- Return: `Final Decision: **Sell**` | [calculated USD amount]
	# 	- If `token_balance == 0`, then: `Final Decision: **Hold**` .
	# - If the environment is **neutral**, then: `Final Decision: **Hold**`.
	print(decision)
	if decision == 'Buy':
		if dollar_balance > 0:
			buy_quantity = calculate_buy_quantity(dollar_balance, crypto_price)
			action = buy(
				slug=slug,
				amount=buy_quantity,
				price=crypto_price,
				remaining_cryptos=buy_quantity,
			)
		else:
			action = hold(slug=slug)
	elif decision == 'Hold':
		action = hold(slug=slug)
	elif decision == 'Sell':
		if token_balance > 0:
			value = calculate_sell_value(token_balance, crypto_price)
			action = sell(
				slug=slug,
				amount=token_balance,
				price=crypto_price,
				remaining_dollar=value,
			)
		else:
			action = hold(slug=slug)
	else:
		action = 'No decision'

	portfolio_analysis[slug] = {
		'decision': content,
		'dollar_balance': dollar_balance,
		'token_balance': token_balance,
		'crypto_price': crypto_price,
		'action': action,
	}
	print(portfolio_analysis)
	progress.update_status('portfolio_manager', slug, 'Done')
	message = HumanMessage(
		content=json.dumps(portfolio_analysis),
		name='portfolio_manager',
	)

	return {'messages': [message], 'data': data}


def calculate_buy_quantity(dollar_balance: float, crypto_price: float) -> float:
	"""Returns how many tokens can be bought with the given dollar balance and price."""
	return round(dollar_balance / crypto_price, 6)


def calculate_sell_value(token_balance: float, crypto_price: float) -> float:
	"""Returns how much USD can be received by selling tokens at current price."""
	return round(token_balance * crypto_price, 2)


def buy(
	slug: str,
	amount: float,
	price: float,
	remaining_cryptos: float,
	# remaining_dollar: float,
) -> str:
	"""
	Execute a BUY order by inserting into the trades table.
	"""
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_cryptos, remaining_dollar) VALUES (?, 'buy', ?, ?, ?, ?, 0.0)",
		(timestamp, slug, amount, price, remaining_cryptos),
	)
	conn.commit()
	conn.close()
	return f'Executed BUY for {slug} | {amount} @ {price}'


def sell(
	slug: str,
	amount: float,
	price: float,
	remaining_dollar: float,
) -> str:
	"""
	Execute a SELL order by inserting into the trades table.
	"""
	db_path = Path(f'base_workflow/outputs/{slug}_trades.db')
	db_path.parent.mkdir(parents=True, exist_ok=True)
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	timestamp = datetime.utcnow().isoformat()
	cursor.execute(
		"INSERT INTO trades (timestamp, action, slug, amount, price, remaining_cryptos, remaining_dollar) VALUES (?, 'sell', ?, ?, ?, 0.0,?)",
		(timestamp, slug, amount, price, remaining_dollar),
	)
	conn.commit()
	conn.close()
	return f'Executed SELL for {slug} | {amount} @ {price}'


def hold(slug: str) -> str:
	"""
	No trade executed. Hold position.
	"""
	return f'HOLD: No trade executed for {slug}. Position unchanged.'


if __name__ == '__main__':
	llm = get_llm()

	workflow = StateGraph(AgentState)
	workflow.add_node('portfolio_manager', portfolio_manager)
	workflow.set_entry_point('portfolio_manager')
	graph = workflow.compile()

	simulated_signals = {
		'bitcoin': {
			'technical_analyst': {
				'signal': 'bullish',
				'confidence': 0.9,
				'report': 'RSI and MACD show strong upward momentum, with golden cross formation confirmed.',
			},
			'sentiment_analyst': {
				'signal': 'buy',
				'confidence': 0.75,
				'report': "Sentiment is improving, Fear & Greed Index in 'Extreme Fear'.",
			},
			'news_analyst': {
				'signal': 'buy',
				'confidence': 0.8,
				'report': 'Market reacts positively to SEC ETF approval rumors.',
			},
			'risk_manager': {
				'signal': 'hold',
				'confidence': 0.6,
				'report': 'Volatility remains high, but no imminent systemic risks.',
			},
		}
	}
	initial_state = {
		'messages': [
			HumanMessage(content='Make trading decisions based on the provided data.'),
			HumanMessage(
				name='aggregated_analysts', content=json.dumps(simulated_signals)
			),
		],
		'data': {
			'token': 'BTC',
			'slug': 'bitcoin',
			'dollar balance': 2000000,  # initial capital in USD
			'token balance': 0,  # initial token balance
			'close_price': 30000,  # current market price of BTC
			'start_date': '2024-06-07',
			'end_date': '2024-06-21',
			'time_interval': '4h',
		},
		'metadata': {'request_id': 'test-456', 'timestamp': '2025-07-11T12:00:00Z'},
	}

	final_state = graph.invoke(initial_state)
	# final_decision = final_state['data']['Portfolio manager']
