from turtle import update
from base_workflow.agents import social_media_analyst
from langchain_core.messages import HumanMessage
from langgraph.types import Command
# from langgraph.graph import MessagesState
from typing import Literal
from agents.state import AgentState


def social_media_analyst_node(state: AgentState) -> Command[Literal["news_analyst"]]:
    result = social_media_analyst.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="doc_writer")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="news_analyst",
    )
