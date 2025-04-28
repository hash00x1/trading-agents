from base_workflow.agents import crypto_manager
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal

class State(MessagesState):
    next: str

def crypto_manager_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = crypto_manager.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="web_scraper")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="supervisor",
    )