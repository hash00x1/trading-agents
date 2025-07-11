from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from typing import Optional
from base_workflow.graph.state import AgentState

def create_aggressive_risk_debator(
    model: ChatOpenAI,
    tool_names: Optional[list[str]] = None
):
    aggressive_risk_debator_system_message = SystemMessage(content="""
    You are the Aggressive Risk Debator, tasked with pushing the boundaries of the firm’s risk tolerance.
    Your role is to maximize growth potential by encouraging high-risk, high-reward positions, 
    while still operating within regulatory and system-defined constraints. 
    You assess risk factors like volatility and counterparty exposure, but you favor aggressive strategies such as leveraged positions or concentration in volatile assets.
    Provide critical feedback to the Trader Agent when current strategies are too conservative. Prioritize opportunity over caution, 
    but always provide a justification for your higher-risk tolerance. Collaborate with other agents via shared environment state, 
    and take ReAct-style actions that reflect an assertive risk appetite.
    """)

    if tool_names:
        return DialogueAgentWithTools(
            name="Aggressive Risk Debator",
            system_message=aggressive_risk_debator_system_message,
            model=model,
            tool_names=tool_names
        )
    else:
        return DialogueAgent(
            name="Aggressive Risk Debator",
            system_message=aggressive_risk_debator_system_message,
            model=model,
        )

