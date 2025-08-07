from base_workflow.agents.debate_agent import DialogueSimulatorAgent
from base_workflow.agents import create_bearish_researcher, create_bullish_researcher
from typing import List
from base_workflow.graph.state import AgentState
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional
from typing_extensions import Literal
import json
from typing import Any
from base_workflow.utils.progress import progress
import re
from base_workflow.utils.llm_config import get_llm


class ResearchReport:
	signal: Literal['Buy', 'Sell', 'Hold']
	report: str


# change this to support different slug
class ResearchManager(DialogueSimulatorAgent):
	def __init__(self, rounds: int, state: Optional[AgentState] = None):
		self.research_analysis: dict[str, Any] = {}
		self.model = get_llm()
		# self.data = state["data"]

		if state is None:
			state = AgentState(messages=[], data={}, metadata={})

		research_agents = [
			create_bullish_researcher(model=self.model),
			create_bearish_researcher(model=self.model),
		]
		super().__init__(agents=research_agents, name='Research Manager', rounds=rounds)

	def generate_report(self, conversation_log: List[tuple[str, str]]):
		system_msg = """
        You are the Research Manager in a multi-agent crypto trading system. 
		Your will receive a debate conversation log between a Bullish Researcher and a Bearish Researcher.
		Your tasks are:
			1. carefully review the debate conversation log
			2. make a clear and actionable decision based on the strength and coherence of their arguments, choose one of the following options:
				- Align with the **Bullish Researcher** → if their case is more compelling.
				- Align with the **Bearish Researcher** → if their reasoning is stronger.
			
			3. write a report to present your decision and reasoning.
        
		The report should follow this structure:
        
		---

		## Research Debate Evaluation Report

		### 1. Summary of Bullish Researcher’s Arguments
		- [Summarize key bullish points.]

		### 2. Summary of Bearish Researcher’s Arguments
		- [Summarize key bearish points.]

		### 3. Evaluation of Arguments
		- **Bullish Strengths:** [What is strong or well-supported?]
		- **Bullish Weaknesses:** [Any flaws, gaps, or overstatements?]
		- **Bearish Strengths:** [What is strong or well-supported?]
		- **Bearish Weaknesses:** [Any flaws, gaps, or overstatements?]
		- **Balance of Reasoning:** [Compare both sides: who was more convincing and why?]

		### 4. Final Decision
		- **Final Decision:** **Buy / Sell**

		- **Justification:** [Clearly state why this position is more reasonable, based on your evaluation.]

		---

            Please return only the research report, formatted using Markdown-style headers.
        """
		human_msg = HumanMessage(
			content=f"""Here is the conversation log between the Bullish Researcher and Bearish Researcher: {conversation_log}"""
		)
		# Call the LLM to get the analysis
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
	print(reply)
