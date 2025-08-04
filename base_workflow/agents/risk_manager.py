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
import re


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
		system_msg = """
        You are a Risk Manager in a crypto-focused multi-agent financial system.
		Your role is to evaluate and synthesize the perspectives of three specialized debaters:
		- The Aggressive Risk Debater
		- The Neutral Risk Debater
		- The Conservative Risk Debater
        
		Your responsibilities:

		1. Carefully read the debate messages from these three agents in the current conversation history.
		2. Identify each debater’s core arguments, risk assumptions, and justifications.
		3. Determine the key points of disagreement or conflict among them.
		4. Analyze the logical consistency, empirical strength, and practical implications of each viewpoint.
		5. Provide a detailed report explaining your judgment and risk recommendation.

        The report should follow this structure:
        
			## Risk Debate Evaluation Report

			### 1. Summary of Aggressive Risk Debater’s Arguments
			- [Summarize high-risk-tolerance views, focus on upside bias.]

			### 2. Summary of Neutral Risk Debater’s Arguments
			- [Summarize balanced considerations, moderate risk outlook.]

			### 3. Summary of Conservative Risk Debater’s Arguments
			- [Summarize cautionary views, highlight risk-averse concerns.]

			### 4. Evaluation of Arguments

			#### High-Risk Indicators
			- Summarize the key concerns raised by the Conservative Risk Debater.
			- Include any warnings about macroeconomic risks, regulatory threats, liquidity issues, or signs of market instability.
			- Emphasize data or arguments indicating significant downside risk or loss potential.

			#### Low-Risk Indicators
			- Summarize the arguments made by the Aggressive Risk Debater suggesting minimal risk.
			- Highlight points about strong upside potential, undervaluation, improving fundamentals, or resilient market conditions.
			- Include references to confidence in current trend continuation or positive momentum.

			#### Neutral Risk Factors
			- Present the observations from the Neutral Risk Debater.
			- Highlight any balanced or undecided views, hedged opinions, or uncertainty due to insufficient data.
			- Discuss where the debater acknowledged both upside and downside without firm conclusions.

			#### Balance of Reasoning
			- Compare the overall persuasiveness of each viewpoint.
			- Evaluate which debater offered the most coherent, well-supported, and logically consistent argument.
			- Identify if one side underestimated or overestimated the risks, and conclude which view most accurately represents the risk outlook.


			### 5. Final Decision
			- **Trading Signal:** **Buy / Hold / Sell**
			- **Justification:** [Clearly explain why this decision is best aligned with the overall risk outlook.]
			You must avoid defaulting to Hold as a compromise, only if neither the aggressive nor conservative positions provide sufficient justification for action. 
			In most cases, you are expected to make a firm decision — **either Buy or Sell** — based on which side presented stronger reasoning and evidence.

            Please return only the research report, formatted using Markdown-style headers.
        """

		human_msg = HumanMessage(
			content=f"""Here is the conversation log between the Aggressive Risk Debater, the Neutral Risk Debater and the Conservative Risk Debater: {conversation_log}"""
		)
		# Step 1: Ask model to generate report
		response_msg = self.model.invoke([SystemMessage(content=system_msg), human_msg])
		content = str(response_msg.content)
		match_signal = re.search(r'(?i)final decision\W*\**\s*(buy|sell)\**', content)

		if match_signal:
			match_signal = match_signal.group(1).capitalize()
		else:
			match_signal = 'Hold'

		self.research_analysis = {
			'signal': match_signal,
			'report': content,
		}
		message = HumanMessage(
			content=json.dumps(self.research_analysis), name='risk_manager'
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


risk_manager = RiskManager(rounds=4)


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
	print(reply)
