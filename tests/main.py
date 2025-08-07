from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import init
from base_workflow.agents import (
	technical_analyst,
	news_analyst,
	on_chain_analyst,
	social_media_analyst,
	research_manager,
	risk_manager,
	portfolio_manager,
)
from base_workflow.tools import buy, sell, hold, read_trades
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from reset import load_symbol_slug_mapping_from_file
import json
from datetime import datetime, timedelta
from base_workflow.utils.llm_config import get_llm


# Load environment variables from .env file
load_dotenv()

init(autoreset=True)

# define hedging tool node
TOOLS = [buy, sell, hold]

llm = get_llm()
llm_with_tools = llm.bind_tools(TOOLS)


# def hedging_tool_node(inputs: Dict[str, Any]) -> Dict[str, Any]:
# 	# LLM generates an instruction indicating which tool it wants to call and with what parameters
# 	user_input = inputs.get('Portfolio manager')
# 	ai_msg = llm_with_tools.invoke(user_input)
# 	calls = ai_msg.tool_calls
# 	if not calls:
# 		return ai_msg.content


# 	# Only one tool is used, based on the logic now
# 	call = calls[0]
# 	fn = next(t for t in TOOLS if t.name == call['name'])
# 	return fn.invoke(call['args'])
# def hedging_tool_node(state: AgentState) -> dict:
# 	input = state['data']['Portfolio manager']

# 	if not isinstance(input, str) or not input.strip():
# 		return {'error': "Missing or invalid 'Portfolio manager' input."}

# 	try:
# 		ai_msg = llm_with_tools.invoke(input)
# 	except Exception as e:
# 		return {'error': f'LLM invocation failed: {str(e)}'}

# 	calls = ai_msg.tool_calls
# 	if not calls:
# 		return {'result': ai_msg.content}

# 	call = calls[0]
# 	fn = next((t for t in TOOLS if t.name == call['name']), None)
# 	if not fn:
# 		return {'error': f"Tool '{call['name']}' not found."}

# 	try:
# 		tool_result = fn.invoke(call['args'])
# 	except Exception as e:
# 		return {'error': f'Tool execution failed: {str(e)}'}

# 	return {
# 		'tool_name': call['name'],
# 		'tool_args': call['args'],
# 		'tool_result': tool_result,
# 	}


# for cmd in [
#     'Buy 0.2 BTC at 29000, remains are 100000 dollar',  # unify all the writing style in portfolio_manager at outputs
#     'Sell 1 ETH at 1850, remains are 1345000 dollar',
#     'Hold DOGE',
# ]:
#     # only one command would be given in one round.
#     print(f'\n> {cmd}')
#     output = hedging_tool_node(cmd)
#     print(output)


def parse_response(response):
	"""Parses a JSON string and returns a dictionary."""
	try:
		return json.loads(response)
	except json.JSONDecodeError as e:
		print(f'JSON decoding error: {e}\nResponse: {repr(response)}')
		return None
	except TypeError as e:
		print(
			f'Invalid response type (expected string, got {type(response).__name__}): {e}'
		)
		return None
	except Exception as e:
		print(
			f'Unexpected error while parsing response: {e}\nResponse: {repr(response)}'
		)
		return None


##### Run the Crypto Agents Team #####
def run(
	start_date: str,
	end_date: str,
	time_interval: str = '4h',
	show_reasoning: bool = False,
):
	# Start progress tracking
	progress.start()

	try:
		# Create a new workflow if analysts are customized
		agent = app
		# read in wallet. one for dollar, one for token.
		# 因为这里没有限制，暂时先不支持token之间的交互。因为如果一次只处理一个slug的话，比较难进行slug之间的比较。先分开处理。
		tokens = [
			'BTC',
			'ETH',
			'PEPE',
			'DOGE',
			'USDT',
		]  # bag of tokens -> generate randomly, or predefined.
		# "bitcoin", "pepe", "dogecoin", 'ethereum', 'tether'
		# slugs = [ 'bitcoin', 'ethereum', 'cardano', 'solana', 'chainlink']
		# 只选择能测试的。

		symbol_to_slug = load_symbol_slug_mapping_from_file()
		token_slug_map = {token: symbol_to_slug.get(token.upper()) for token in tokens}
		# slugs = [symbol_to_slug.get(token.upper()) for token in tokens]
		results = {}
		for (
			token,
			slug,
		) in token_slug_map.items():  # invoke for each slug and write to wallet
			df = read_trades(
				slug
			)  # read in wallet， read in the last state of the wallet.
			dollar_balance = df['remaining_dollar'].iloc[0]
			token_balance = df['remaining_cryptos'].iloc[0]
			final_state = agent.invoke(
				{
					'messages': [
						HumanMessage(
							content='Make trading decisions based on the provided data.',
						)
					],
					'data': {
						'token': token,
						'slug': slug,
						'dollar balance': dollar_balance,
						'token balance': token_balance,
						'start_date': start_date,
						'end_date': end_date,
						'time_interval': time_interval,
					},
					'metadata': {'show_reasoning': show_reasoning},
				},
			)
			results[token] = {
				'messages': final_state['messages'],
				'data': final_state['data'],
			}

		return results  # if return not alined with for, then only the first token will be tested. Note for test use.
		# -> use finale_state to update wallet -> wallet.update

	finally:
		progress.stop()


def start(state: AgentState):
	"""Initialize the workflow with the input message."""
	return state


def create_workflow(selected_analysts=None):
	"""Create the workflow with selected analysts."""
	workflow = StateGraph(AgentState)
	workflow.add_node('technical_analyst', technical_analyst)
	workflow.add_node('social_media_analyst', social_media_analyst)
	workflow.add_node('news_analyst', news_analyst)
	workflow.add_node('on_chain_analyst', on_chain_analyst)
	workflow.add_node('research_manager', research_manager)
	workflow.add_node('risk_manager', risk_manager)
	workflow.add_node(
		'portfolio_manager', portfolio_manager
	)  # -> needs error handlng when amount of tokens bough it larger than dollars available

	# Define the workflow edges of research team
	workflow.set_entry_point('technical_analyst')
	workflow.add_edge('technical_analyst', 'social_media_analyst')
	workflow.add_edge('social_media_analyst', 'news_analyst')
	workflow.add_edge('news_analyst', 'on_chain_analyst')
	workflow.add_edge('on_chain_analyst', 'research_manager')
	workflow.add_edge('research_manager', 'risk_manager')
	workflow.add_edge('risk_manager', 'portfolio_manager')
	workflow.add_edge('portfolio_manager', END)
	return workflow


if __name__ == '__main__':
	end_date = datetime.utcnow()
	start_date = end_date - timedelta(days=30)
	start_str = start_date.strftime('%Y-%m-%d')
	end_str = end_date.strftime('%Y-%m-%d')

	# Create the workflow with selected analysts
	workflow = create_workflow()
	app = workflow.compile()

	# Run the hedge fund
	result = run(
		start_date=start_str,
		end_date=end_str,
		time_interval='4h',
		show_reasoning=False,
	)
