import json
from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph
import re


def portfolio_manager(state: AgentState):
	messages = state.get('messages', [])
	data = state.get('data', {})
	slugs = data.get('slugs', [])
	llm = ChatOpenAI(model='gpt-4o')
	decisions = {}

	for slug in slugs:
		progress.update_status(
			'portfolio_manager', slug, 'Aggregating multi-agent signals and deciding.'
		)

		analyst_summary_prompt = f"""
        You are a crypto portfolio manager in a multi-agent system.
        For the asset **{slug}**, you have received signal reports from different analysts (technical, sentiment, on-chain, research, risk, news, etc.).
        You currently have {dollars} in your wallet, the current market price of {slug} is {price_data}.
		Your task is to synthesize these insights and give ONE final decision, in structured format:
        ---
        ### Final Decision (REQUIRED)
        Provide one final trading signal:

        `Final Decision: **Buy**`  | + quantity
        `Final Decision: **Hold**`  | + quantity
        `Final Decision: **Sell**`  | + quantity

        Please keep the format consistent and clean. Do not include any additional output.
		You have access to the following tools:
		Calculate_Amount: "Description"
		Buy: ""
		Sell: ""
		Hold: "" -> defined as return None 
		def Hold:
            return None
        """
		portfolio_decision_agent = create_react_agent(
			llm, tools=[], state_modifier=analyst_summary_prompt
		)

		response = portfolio_decision_agent.invoke({'messages': messages})
		content = response['messages'][-1].content
		match_signal = re.search(r'Final Decision: \*\*(Buy|Hold|Sell)\*\*', content)
		decisions[slug] = {'signal': match_signal.group(1) if match_signal else None}
		progress.update_status('portfolio_manager', slug, 'Done')

		print(f'{decisions}\n')

	return {'decisions': decisions}


d
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
			'slugs': ['bitcoin'],
			'start_date': '2024-06-07',
			'end_date': '2024-06-21',
			'time_interval': '4h',
		},
		'metadata': {'request_id': 'test-456', 'timestamp': '2025-07-11T12:00:00Z'},
	}

	final_state = graph.invoke(initial_state)

	print(final_state)
