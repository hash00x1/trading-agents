from base_workflow.agents import news_analyst
from langchain_core.messages import HumanMessage
from langgraph.types import Command
# from langgraph.graph import MessagesState
from typing import Literal
from base_workflow.state import AgentState

    
def news_analyst_node(state: AgentState) -> Command[Literal["fundamentals_analyst"]]:
	result = news_analyst.invoke(state)
	return Command(
		update={
			'messages': [
				HumanMessage(content=result["messages"][-1].content, name='search')
			]
		},
		# We want our workers to ALWAYS "report back" to the supervisor when done
		goto="fundamentals_analyst"
		)