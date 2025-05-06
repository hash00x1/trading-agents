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
from base_workflow.nodes import (market_analyst_node, social_media_analyst_node, news_analyst_node, fundamentals_analyst_node)
from agents.state import AgentState
# from base_workflow.agents import aggressive_agent, bearish_researcher, bullish_researcher, trader
# from base_workflow.utils import DialogueAgentWithTools
# from base_workflow.utils.debate_agent import DialogueSimulator

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("TAVILY_API_KEY")

class State(MessagesState):
    next: str


llm = ChatOpenAI(model="gpt-4o")

workflow = StateGraph(AgentState)

workflow.add_node("market_analyst", market_analyst_node)
workflow.add_node("social_media_analyst", social_media_analyst_node)
workflow.add_node("news_analyst", news_analyst_node)
workflow.add_node("fundamentals_analyst", fundamentals_analyst_node)

# Define the workflow edges of research team
workflow.set_entry_point("market_analyst")
workflow.add_edge("market_analyst", "social_media_analyst")
workflow.add_edge("social_media_analyst", "news_analyst")
workflow.add_edge("news_analyst", "fundamentals_analyst")
# workflow.add_node("bearish_researcher", bearish_researcher)
# workflow.add_node("bullish_researcher", bullish_researcher)
# workflow.add_node("trader", trader)
# workflow.add_node("aggressive_agent", aggressive_agent)
# workflow.add_node("neutral_agent", neutral_agent)
# workflow.add_node("conservative_agent", conservative_agent)
# workflow.add_node("manager", manager)



# analyst to researcher
# workflow.set_entry_point("market_analyst", "bearish_researcher")
# workflow.add_edge("social_media_analyst", "bearish_researcher")
# workflow.add_edge("news_analyst", "bearish_researcher")
# workflow.add_edge("fundamentals_analyst", "bearish_researcher")

# workflow.add_edge("market_analyst", "bullish_researcher")
# workflow.add_edge("social_media_analyst", "bullish_researcher")
# workflow.add_edge("news_analyst", "bullish_researcher")
# workflow.add_edge("fundamentals_analyst", "bullish_researcher")

# workflow.add_edge("market_analyst", "bullish_researcher")
# workflow.add_edge("social_media_analyst", "bullish_researcher")
# workflow.add_edge("news_analyst", "bullish_researcher")
# workflow.add_edge("fundamentals_analyst", "bullish_researcher")

# # Define the workflow edges of research team to trader
# workflow.add_edge("bearish_researcher", "trader")
# workflow.add_edge("bullish_researcher", "trader")

# # Define the workflow edges of trader to debate team
# workflow.add_edge("trader", "aggressive_agent")
# workflow.add_edge("trader", "neutral_agent")
# workflow.add_edge("trader", "conservative_agent")

# # Define the workflow edges of debate team to manager
# workflow.add_edge("aggressive_agent", "manager")
# workflow.add_edge("neutral_agent", "manager")
# workflow.add_edge("conservative_agent", "manager")


research_graph = workflow.compile()
if __name__ == '__main__':
    for s in research_graph.stream(
        {"messages": [("user", "Can you analysis current tendency of Apple Inc.'s stock price?")]},
        #subgraphs=True,
        {"recursion_limit": 10}):
        print(s)
        print("---")