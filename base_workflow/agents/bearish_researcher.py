from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from typing import Optional
from base_workflow.graph.state import AgentState

def create_bearish_researcher(
    model: ChatOpenAI,
    tool_names: Optional[list[str]] = None
):
    bearish_researcher_system_message = SystemMessage(content="""
    You are a Bearish Researcher. 
    Your role is to focus on potential downsides, risks, and unfavorable market signals. 
    You should argue that investments in certain assets could have negative outcomes due to market volatility, economic downturns, or poor growth potential. 
    Provide cautionary insights to convince others not to invest or to consider risk management strategies.
    """)

    if tool_names:
        return DialogueAgentWithTools(
            name="Bearish Researcher",
            system_message=bearish_researcher_system_message,
            model=model,
            tool_names=tool_names
        )
    else:
        return DialogueAgent(
            name="Bearish Researcher",
            system_message=bearish_researcher_system_message,
            model=model,
        )

