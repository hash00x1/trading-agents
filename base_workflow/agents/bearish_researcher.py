from pyclbr import Class
from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage

from base_workflow.agents import news_analyst
from langchain_core.messages import HumanMessage
from langgraph.types import Command
# from langgraph.graph import MessagesState
from typing import Literal
from base_workflow.graph.state import AgentState

llm = ChatOpenAI(model="gpt-4o")
bearish_researcher_system_message = """
You are a Bearish Researcher. 
Your role is to focus on potential downsides, risks, and unfavorable market signals. 
You should argue that investments in certain assets could have negative outcomes due to market volatility, economic downturns, or poor growth potential. Provide cautionary insights to convince others not to invest or to consider risk management strategies.
"""

def create_bearish_researcher(state: AgentState):
    agent = DialogueAgent(
        name="Bearish Researcher",
        system_message=SystemMessage(content=bearish_researcher_system_message),
        model=llm,
        state=state
    )
    
    message_content = agent.send()
    # change later
    return agent.state
