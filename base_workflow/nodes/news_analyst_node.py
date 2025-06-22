from langchain_core.messages import HumanMessage
from langgraph.types import Command
from typing import Literal
from base_workflow.graph.state import AgentState
from base_workflow.agents import news_analyst

def news_analyst_node(state: AgentState) -> Command[Literal["technical_analyst"]]:
    result = news_analyst.invoke(state)
    return Command(
        update={
            'messages': [
                HumanMessage(content=result["messages"][-1].content, name='news')
            ],
            'news_report': result["messages"][-1].content
        },
        goto='technical_analyst'
    )
