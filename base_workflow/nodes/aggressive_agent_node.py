from base_workflow.agents import aggressive_agent
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal

class State(MessagesState):
    next: str
    
def aggressive_agent_node(state: MessagesState) -> Command[Literal['supervisor']]:
	result = aggressive_agent.invoke(state)
	return Command(
		update={
			'messages': [
				HumanMessage(content=result["messages"][-1].content, name='search')
			]
		},
		# We want our workers to ALWAYS "report back" to the supervisor when done
		goto='supervisor'
	)
