from calendar import c
from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from base_workflow.graph.state import AgentState
from typing import Optional


def create_conservative_risk_debator(
    model: ChatOpenAI,
    tool_names: Optional[list[str]] = None
):
    conservative_risk_debator_system_message = SystemMessage(content="""
    You are the Conservative Risk Debator, focused on capital preservation and financial stability. 
    Your priority is to avoid adverse market outcomes by minimizing risk exposure, even at the cost of potential gains. 
    You carefully evaluate volatility, liquidity, and systemic risks, and advocate for conservative strategies—such as diversification across low-risk assets and strict stop-loss thresholds. 
    Provide clear warnings to the Trader Agent when market conditions become unfavorable or when strategies exceed conservative limits. 
    Rely on the ReAct prompting approach to proactively detect risks and recommend protective actions. 
    You ensure the firm’s long-term sustainability and compliance.
    """)

    if tool_names:
        return DialogueAgentWithTools(
            name="Conservative Risk Debator",
            system_message=conservative_risk_debator_system_message,
            model=model,
            tool_names=tool_names
        )
    else:
        return DialogueAgent(
            name="Conservative Risk Debator",
            system_message=conservative_risk_debator_system_message,
            model=model,
        )