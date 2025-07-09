from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from base_workflow.graph.state import AgentState
from typing import Optional

def create_bullish_researcher(
    model: ChatOpenAI, 
    state: AgentState, 
    tool_names: Optional[list[str]] = None
):
    bullish_researcher_system_message = SystemMessage(content="""
    You are a Bullish Researcher. Your role is to highlight positive indicators, growth potential, and favorable market conditions. 
    You advocate for investment opportunities by emphasizing high growth, strong fundamentals, and positive market trends. 
    You should encourage others to initiate or continue positions in certain assets.
    """)
    if tool_names:
        return DialogueAgentWithTools(
            name="Bullish Researcher",
            system_message=bullish_researcher_system_message,
            model=model,
            state=state,
            tool_names=tool_names
        )
    else:
        return DialogueAgent(
            name="Bullish Researcher",
            system_message=bullish_researcher_system_message,
            model=model,
            state=state
        )

