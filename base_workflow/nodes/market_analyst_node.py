# Helper function to create a node for a given agent
from turtle import update
from langchain_core.messages import HumanMessage
from base_workflow.agents import market_analyst
from langgraph.types import Send, Command
from langgraph.graph import MessagesState
from typing import Literal

class State(MessagesState):
    next: str
    
def market_analyst_node(state: MessagesState) -> Command[Literal["social_media_analyst"]]:
	result = market_analyst.invoke(state)
	return Command(
		update={
			'messages': [
				HumanMessage(content=result["messages"][-1].content, name='search')
			]
		},
		goto="social_media_analyst"
		)

