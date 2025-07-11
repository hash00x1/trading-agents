from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from base_workflow.graph.state import AgentState
from typing import Optional

def create_neutral_risk_debator(
    model: ChatOpenAI,
    tool_names: Optional[list[str]] = None
):
    neutral_risk_debator_system_message = SystemMessage(content="""
    You are the Neutral Risk Debator, responsible for maintaining a balanced and pragmatic risk profile. 
    Your goal is to ensure the portfolio stays aligned with both risk tolerance and investment objectives without leaning too conservative or aggressive. 
    Continuously monitor market conditions, liquidity, and counterparty risks, and provide data-driven feedback to the Trader Agent. 
    Suggest mitigation strategies like moderate stop-loss orders and portfolio diversification. 
    You operate as a stabilizing force in the team, seeking sustainable performance. 
    Use the ReAct framework to reason through market events and respond with well-measured risk management actions.
    """)

    if tool_names:
        return DialogueAgentWithTools(
            name="Neutral Risk Debator",
            system_message=neutral_risk_debator_system_message,
            model=model,
            tool_names=tool_names
        )
    else:
        return DialogueAgent(
            name="Neutral Risk Debator",
            system_message=neutral_risk_debator_system_message,
            model=model,
        )
    