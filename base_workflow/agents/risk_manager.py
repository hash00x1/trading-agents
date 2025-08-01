from base_workflow.agents.debate_agent import DialogueSimulatorAgent
from langchain_openai import ChatOpenAI
from base_workflow.agents import (
	create_aggressive_risk_debator,
	create_conservative_risk_debator,
	create_neutral_risk_debator,
)
from base_workflow.graph.state import AgentState
from langchain.schema import SystemMessage, HumanMessage
from typing import Any
from typing import Optional
import json
from base_workflow.utils.progress import progress


class RiskManager(DialogueSimulatorAgent):
	def __init__(self, rounds: int, state: Optional[AgentState] = None):
		self.research_analysis: dict[str, Any] = {}
		self.model = ChatOpenAI(model='gpt-4o', temperature=0.7)

		if state is None:
			state = AgentState(messages=[], data={}, metadata={})

		debator_agents = [
			create_aggressive_risk_debator(model=self.model),
			create_conservative_risk_debator(model=self.model),
			create_neutral_risk_debator(model=self.model),
		]
		super().__init__(agents=debator_agents, name='Risk Manager', rounds=rounds)

	def generate_report(self, conversation_log: list[tuple[str, str]]):
		analysis_prompt = f"""
        You are a financial risk assistant. Your task is to read the conversation log between
        an Aggressive Risk Debator, a Conservative Risk Debator, and a Neutral Risk Debator.
        Based on this multi-round debate, please generate a structured risk analysis report
        to assist a trader in managing portfolio risks. In the last section of the report,
        you must give an actionable risk-based trading signal.

        Conversation Log:
        {conversation_log}

        The report should follow this structure:
        
            # Executive Summary
            Briefly summarize the overall risk outlook, the key risk factors discussed, and the final recommendation (Buy / Sell / Hold).
            Keep it concise (3–5 lines), so a portfolio manager can quickly understand the core points.

            # Risk Factors
            ## High-Risk Indicators
            List concerns raised by the Conservative Risk Debator or data suggesting high downside risk.

            ## Low-Risk Indicators
            List arguments made by the Aggressive Risk Debator or indicators of limited risk.

            ## Neutral Risk Factors
            Summarize balanced or uncertain views from the Neutral Risk Debator.

            # Quantitative Risk Metrics
            If any were discussed, list numerical risk indicators (e.g., volatility index, Sharpe ratio, drawdowns).

            # Macroeconomic or External Influences
            Summarize qualitative insights such as macroeconomic conditions, regulatory risks, or market sentiment.

            # Metadata Summary
            Include context details like:
            - Assets discussed
            - Time interval
            - Date range
            - Tools or sources referenced

            # Final Recommendation
            - Based on the report above, provide a clear trading signal.
            - Format: `Trading Signal: **Buy** / **Hold** / **Sell**`
            - Please return only the signal in that section.

            Return only the full report in markdown-style formatting.
        """

		# Step 1: Ask model to generate report
		report_msg = self.model.invoke(
			[
				SystemMessage(content='You are a financial risk report assistant.'),
				HumanMessage(content=analysis_prompt),
			]
		)
		report = report_msg.content

		# Step 2: Extract trading signal only
		signal_prompt = f"""
        Based on the following risk report, extract the final trading signal only.

        {report}

        Return a single line in this format:
        Trading Signal: **Buy** / **Sell** / **Hold**
        """

		signal_msg = self.model.invoke([HumanMessage(content=signal_prompt)])
		signal = signal_msg.content

		# Step 3: Store and return as HumanMessage
		self.risk_analysis = {
			'signal': signal,
			'report': report,
		}

		message = HumanMessage(
			content=json.dumps(self.risk_analysis), name='risk_manager'
		)

		return message

	def __call__(self, state: AgentState):
		data = state.get('data', {})
		slug = str(data.get('slug'))

		progress.update_status('risk_manager', slug, 'start debating rounds')
		conversation = super().run(state)
		progress.update_status('risk_manager', slug, 'generating debate results')
		message = self.generate_report(conversation)
		progress.update_status('risk_manager', slug, 'Done')

		return {
			'messages': [message],
			'data': data,
		}


risk_manager = RiskManager(rounds=6)


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
	result = risk_manager.run(test_state)
	reply = risk_manager.generate_report(conversation_log=result)
	print(result)
