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
from langchain_openai import ChatOpenAI
from base_workflow.graph.state import AgentState
from .reset import load_symbol_slug_mapping_from_file
from base_workflow.utils.progress import progress

import json

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)

# define hedging tool node
TOOLS = [buy, sell, hold]

llm = ChatOpenAI(temperature=0)
llm_with_tools = llm.bind_tools(TOOLS)


def hedging_tool_node(user_input: str) -> str:
	# LLM generates an instruction indicating which tool it wants to call and with what parameters
	ai_msg = llm_with_tools.invoke(user_input)
	calls = ai_msg.tool_calls
	if not calls:
		return ai_msg.content

	# assumed only one tool is used, based on the logic now
	call = calls[0]
	fn = next(t for t in TOOLS if t.name == call['name'])
	return fn.invoke(call['args'])


# for cmd in [
#     'Buy 0.2 BTC at 29000, remians are 100000 dollar',  # unify all the writing style in portfolio_manager at outputs
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
	slugs: list[str],
	wallet: list[str],
	start_date: str,
	end_date: str,
	time_interval: str = '4h',
	# portfolio: dict,
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
			'ETH',
			'BTC',
			'ADA',
			'SOL',
		]  # bag of tokens -> generate randomly, or predefined.
		# slugs = ['ethereum', 'bitcoin', 'cardano', 'solana']
		symbol_to_slug = load_symbol_slug_mapping_from_file()
		slugs = [symbol_to_slug.get(token.upper()) for token in tokens]
		for slug in slugs:  # invoke for each slug and write to wallet
			# read in wallet.
			df = read_trades(slug)
			current_wallet = {
				'Dollar Balance': df['remaining_dollar'].iloc[0],
				'Token Balance': df['amount'].iloc[0],
			}
			final_state = agent.invoke(
				{
					'messages': [
						HumanMessage(
							content='Make trading decisions based on the provided data.',
						)
					],
					'data': {
						'slugs': slug,
						'current_wallet': current_wallet,
						'start_date': start_date,
						'end_date': end_date,
						'time_interval': time_interval,
					},
					'metadata': {
						'show_reasoning': show_reasoning,
						# "model_name": model_name,
						# "model_provider": model_provider,
					},
				},
			)
			return {
				'messages': final_state['messages'],
				'data': final_state[
					'data'
				],  # should be a key:value pair token ticker: +/- Balance bought .e.g SOL -> {'SOL': + 10} | withdrwa in dollars from wallet
			}
		# -> use finale_state to update wallet -> wallet.update

	finally:
		progress.stop()


def start(state: AgentState):
	"""Initialize the workflow with the input message."""
	return state


def create_workflow(selected_analysts=None):
	"""Create the workflow with selected analysts."""
	workflow = StateGraph(AgentState)
	workflow.add_node('start_node', start)
	workflow.add_node('technical_analyst', technical_analyst)
	workflow.add_node('social_media_analyst', social_media_analyst)
	workflow.add_node('news_analyst', news_analyst)
	workflow.add_node('on_chain_analyst', on_chain_analyst)
	workflow.add_node('research_manager', research_manager)
	workflow.add_node('risk_manager', risk_manager)
	workflow.add_node('portfolio_manager', portfolio_manager)
	workflow.add_node(
		'hedging_tools', hedging_tool_node
	)  # -> needs error handlng when amount of tokens bough it larger than dollars available
	# workflow.add_node("conditional_node", conditional_node)
	# workflow.add_node("write_db", write_to_db)

	# Define the workflow edges of research team
	workflow.set_entry_point('technical_analyst')
	workflow.add_edge('technical_analyst', 'social_media_analyst')
	workflow.add_edge('social_media_analyst', 'news_analyst')
	workflow.add_edge('news_analyst', 'on_chain_analyst')
	workflow.add_edge('on_chain_analyst', 'research_manager')
	workflow.add_edge('research_manager', 'risk_manager')
	workflow.add_edge('risk_manager', 'portfolio_manager')
	workflow.add_edge(
		'portfolio_manager', 'hedging_tools'
	)  # <- bound to the portfolio tools (s. langchain documentation tools.bind())
	workflow.add_edge('hedging_tools', END)

	# workflow.add_edge("portfolio_manager", "conditional_node")
	# workflow.add_conditional_edges(
	#     "conditional_node",
	#     {
	#         "write_db": "write_db",
	#         END: END,
	#     },
	# )
	# workflow.add_edge("write_db", END)

	workflow.set_entry_point('start_node')
	return workflow


if __name__ == '__main__':
	test_state = AgentState(
		messages=[],
		data={
			'slugs': ['bitcoin'],
			'start_date': '2024-06-07',
			'end_date': '2024-08-08',
			'time_interval': '4h',
		},
		metadata={'show_reasoning': False},
	)

	# Create the workflow with selected analysts
	workflow = create_workflow()
	app = workflow.compile()

	# Run the hedge fund
	result = run(
		slugs=test_state['data']['slugs'],
		start_date=test_state['data']['start_date'],
		end_date=test_state['data']['end_date'],
		time_interval=test_state['data']['time_interval'],
		# portfolio=portfolio,
		show_reasoning=test_state['metadata'].get('show_reasoning', False),
	)
	print(result)  # maybe show resoning
