import getpass
import os
from typing import Literal, Union
from chromadb.utils.rendezvous_hash import Members
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from sympy.strategies.rl import subs
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from base_workflow.nodes import (technical_analyst_node, social_media_analyst_node, news_analyst_node, fundamentals_analyst_node)
from base_workflow.graph.state import AgentState
from base_workflow.nodes import trader_node


def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("TAVILY_API_KEY")

class State(MessagesState):
    next: str


llm = ChatOpenAI(model="gpt-4o")

workflow = StateGraph(AgentState)

workflow.add_node("market_analyst", technical_analyst_node)
workflow.add_node("social_media_analyst", social_media_analyst_node)
workflow.add_node("news_analyst", news_analyst_node)
workflow.add_node("fundamentals_analyst", fundamentals_analyst_node)
workflow.add_node("trader", trader_node)
# Define the workflow edges of research team
workflow.set_entry_point("market_analyst")
workflow.add_edge("market_analyst", "social_media_analyst")
workflow.add_edge("social_media_analyst", "news_analyst")
workflow.add_edge("news_analyst", "fundamentals_analyst")
workflow.add_edge("fundamentals_analyst", "trader")


research_graph = workflow.compile()
if __name__ == '__main__':
    for s in research_graph.stream(
        {"messages": [("user", "Can you analysis current tendency of Apple Inc.'s stock price?")]},
        #subgraphs=True,
        {"recursion_limit": 10}):
        print(s)
        print("---")