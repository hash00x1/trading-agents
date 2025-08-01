import json
from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
from base_workflow.tools import get_real_time_price
from langchain.tools import tool

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
	llm = ChatOpenAI(model='gpt-4o')

	progress.update_status(
		'portfolio_manager', slug, 'Aggregating multi-agent signals and deciding.'
	)

	try:  # if not get the newest price use the latest ohlcv price instead.
		crypto_price = get_real_time_price(token)
	except Exception:
		crypto_price = state['data']['close_price']

	analyst_summary_prompt = f"""
	You are a crypto portfolio manager in a multi-agent system.
	For the asset **{slug}**, you have received signal reports from different analysts (technical, sentiment, on-chain, research, risk, news, etc.).
	You currently have **{dollar_balance}** in your wallet, the correct token balance is **{token_balance}**.
	the current market price of **{slug}** is **{crypto_price}**.

	Based on all the information, first determine the overall environment:
	- Favorable to Buy
	- Favorable to Sell
	- Neutral	

	Then follow this rule:
	- If the environment is **favorable to buy**:
		- If `dollar_balance > 0`, then: 
			- Call `calculate_buy_quantity(dollar_balance, crypto_price)` to get how many tokens can be bought.
			- Return: `Final Decision: **Buy**` | [calculated token quantity]
		- If `dollar_balance == 0`, then: `Final Decision: **Hold**`.
	- If the environment is **favorable to sell**:
		- If `token_balance > 0`, then: 
			- Call `calculate_sell_value(token_balance, crypto_price)` to get how much USD can be received.
			- Return: `Final Decision: **Sell**` | [calculated USD amount]
		- If `token_balance == 0`, then: `Final Decision: **Hold**` .
	- If the environment is **neutral**, then: `Final Decision: **Hold**`.

	You have access to the following tools:

	- `calculate_buy_quantity(dollar_balance, crypto_price)`  
		→ Returns how many tokens can be bought with available USD.

	- `calculate_sell_value(token_balance, crypto_price)`  
		→ Returns how much USD can be received by selling the available tokens.


	Your task is to synthesize these insights and give ONE final decision, in structured format:
	- `Final Decision: **Buy** | [number of tokens]`
	- `Final Decision: **Sell** | [amount in USD]`
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
		tools=[calculate_buy_quantity, calculate_sell_value],
		state_modifier=analyst_summary_prompt,
	)

	response = portfolio_decision_agent.invoke({'messages': messages})
	content = response['messages'][-1].content
	progress.update_status('portfolio_manager', slug, 'Done')
	# match_signal = re.search(r'Final Decision: \*\*(Buy|Hold|Sell)\*\*', content)
	# decisions[slug] = {'signal': match_signal.group(1) if match_signal else None}
	# # Output decision format.
	print(f'Final Decision for {slug}: {content}')
	return {'final_decisions': content}  # final decision only contains the action.


@tool
def calculate_buy_quantity(dollar_balance: float, crypto_price: float) -> float:
	"""Returns how many tokens can be bought with the given dollar balance and price."""
	return round(dollar_balance / crypto_price, 6)


@tool
def calculate_sell_value(token_balance: float, crypto_price: float) -> float:
	"""Returns how much USD can be received by selling tokens at current price."""
	return round(token_balance * crypto_price, 2)


# You have access to the following tools:
# Calculate_Amount: "Description"
# Buy: ""
# Sell: ""
# Hold: "" -> defined as return None
# def Hold:
# 	return None

# define calculation tool.
if __name__ == '__main__':
	llm = ChatOpenAI(model='gpt-4o')

	workflow = StateGraph(AgentState)
	workflow.add_node('portfolio_manager', portfolio_manager)
	workflow.set_entry_point('portfolio_manager')
	graph = workflow.compile()

	simulated_signals = {
		'bitcoin': {
			'technical_analyst': {
				'signal': 'bearish',
				'confidence': 0.7,
				'report': 'Technical indicators like RSI and MACD indicate weakening trend.',
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
			'token': ['BTC'],
			'slugs': ['bitcoin'],
			'dollar balance': 1000000,  # initial capital in USD
			'token balance': 0,  # initial token balance
			'close_price': 30000,  # current market price of BTC
			'start_date': '2024-06-07',
			'end_date': '2024-06-21',
			'time_interval': '4h',
		},
		'metadata': {'request_id': 'test-456', 'timestamp': '2025-07-11T12:00:00Z'},
	}

	final_state = graph.invoke(initial_state)
