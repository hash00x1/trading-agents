# Helper function to create a node for a given agent
from turtle import update
from langchain_core.messages import HumanMessage
from base_workflow.agents import fundamentals_analyst
from langgraph.types import Send, Command
# from langgraph.graph import MessagesState
from typing import Literal
from base_workflow.state import AgentState

    
def fundamentals_analyst_node(state: AgentState) -> Command[Literal['trader']]:
	result = fundamentals_analyst.invoke(state)
	return Command(
		update={
			'messages': [
				HumanMessage(content=result["messages"][-1].content, name='search')
			]
		},
		goto='trader'
		)

