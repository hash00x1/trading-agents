from base_workflow.agents.debate_agent import DialogueSimulatorAgent
from base_workflow.agents import create_bearish_researcher, create_bullish_researcher
from typing import List
from langchain_openai import ChatOpenAI
from base_workflow.graph.state import AgentState
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional
from typing_extensions import Literal
import json
from typing import Any
from base_workflow.utils.progress import progress


class ResearchReport:
	signal: Literal['Buy', 'Sell', 'Hold']
	report: str


# change this to support different slug
class ResearchManager(DialogueSimulatorAgent):
	def __init__(self, rounds: int, state: Optional[AgentState] = None):
		self.research_analysis: dict[str, Any] = {}
		self.model = ChatOpenAI(model='gpt-4o', temperature=0.7)
		# self.data = state["data"]

		if state is None:
			state = AgentState(messages=[], data={}, metadata={})

		research_agents = [
			create_bullish_researcher(model=self.model),
			create_bearish_researcher(model=self.model),
		]
		super().__init__(agents=research_agents, name='Research Manager', rounds=rounds)

	def generate_report(self, conversation_log: List[tuple[str, str]]):
		analysis_prompt = f"""
        You are a financial analyst assistant. Your task is to read the conversation log between
        a Bullish Researcher and a Bearish Researcher. Based on this multi-round debate, please generate
        a structured research report to assist a trader in making an informed trading decision,
        in the last chapter on the report, you must give a actionable signal.

        Conversation Log:
        {conversation_log}

        The report should follow this structure:
        
            # Executive Summary
            Briefly summarize the overall market outlook, key talking points, and your final recommendation (Buy / Sell / Hold). 
            This should be concise (3–5 lines), easy to read, and understandable to a portfolio manager.

            # Market Signals
            ## Bullish Signals
            List arguments or indicators supporting a positive outlook. Reference specific insights or arguments from the Bullish Researcher.

            ## Bearish Signals
            List arguments or indicators supporting a negative outlook. Reference specific insights or arguments from the Bearish Researcher.

            ## Quantitative Analysis
            Summarize any numerical indicators discussed or implied (e.g., RSI, MACD, volume trends, volatility).

            # Sentiment & Fundamental Factors
            Summarize qualitative insights (e.g., macro trends, news impact, regulatory changes, social sentiment, research articles) 
            derived from the conversation or tools used.

            # Data Summary
            List metadata related to the analysis:
            - Assets discussed
            - Time interval
            - Date range
            - Tools or sources used by agents (e.g., arxiv, wikipedia)

            # Final Recommendation
            - Based on the report above, provide a clear trading signal.
            - The format must be: `Trading Signal: **Buy** / **Hold** / **Sell**`
            - Please return only the signal, no explanation.

            Please return only the research report, formatted using Markdown-style headers.
        """

		# Call the LLM to get the analysis
		report_msg = self.model.invoke(
			[
				SystemMessage(
					content='You are a financial report assistant. Your task is...'
				),
				HumanMessage(content=analysis_prompt),
			]
		)
		report = report_msg.content
		signal_prompt = f"""
            Based on the following report, output the final trading signal only.

            {report}

            Please return only one line in this format:
            Trading Signal: **Buy** / **Sell** / **Hold**
            """
		signal_msg = self.model.invoke([HumanMessage(content=signal_prompt)])
		signal = signal_msg.content
		self.research_analysis = {
			'signal': signal,
			'report': report,
		}

		message = HumanMessage(
			content=json.dumps(self.research_analysis), name='research_manager'
		)

		return message

	def __call__(self, state: AgentState):
		data = state.get('data', {})
		slug = str(data.get('slug'))
		progress.update_status('research_manager', slug, 'start debating rounds')
		conversation = super().run(state)
		progress.update_status('research_manager', slug, 'generating report')
		message = self.generate_report(conversation)
		progress.update_status('research_manager', slug, 'Done')
		return {
			'messages': [message],
			'data': data,
		}


research_manager = ResearchManager(rounds=6)

# Test the Trader agent
if __name__ == '__main__':
	test_state = AgentState(
		messages=[],
		data={
			'tickers': ['ohlcv/bitcoin'],
			'start_date': '2024-06-07',
			'end_date': '2024-08-08',
			'time_interval': '4h',
		},
		metadata={'show_reasoning': False},
	)
	initial_knowledge = (
		"Please discuss Bitcoin's investment potential over the next 6 months."
	)
	result = research_manager.run(test_state)
	reply = research_manager.generate_report(conversation_log=result)
	print(result)
