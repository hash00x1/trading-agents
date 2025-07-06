# Helper function to create a node for a given agent
from turtle import update
from langchain_core.messages import HumanMessage
from base_workflow.agents import technical_analyst
from langgraph.types import Send, Command
# from langgraph.graph import MessagesState
from typing import Literal
from base_workflow.graph.state import AgentState

    
#def market_analyst_node(state: AgentState) -> Command[Literal["social_media_analyst"]]:
# only for test of bearish_researcher_node
def technical_analyst_node(state: AgentState) -> Command[Literal["social_media_analyst"]]: 
	result = technical_analyst.invoke(state)
	return Command(
		update={
			'messages': [
				HumanMessage(content=result["messages"][-1].content, name='search')
			]
		},
		goto='social_media_analyst'
		)

