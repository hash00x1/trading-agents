from turtle import update
from base_workflow.agents import trader
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal

class State(MessagesState):
    next: str

def trader_node(state: State) -> Command[Literal["supervisor"]]:
    result = trader.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="doc_writer")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )
