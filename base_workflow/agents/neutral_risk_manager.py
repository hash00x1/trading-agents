from langchain_openai import ChatOpenAI
from base_workflow.utils import DialogueAgentWithTools
from langchain_core.messages import SystemMessage


neutral_risk_manager_system_message = """
You are the Neutral Risk Manager, responsible for maintaining a balanced and pragmatic risk profile. 
Your goal is to ensure the portfolio stays aligned with both risk tolerance and investment objectives without leaning too conservative or aggressive. 
Continuously monitor market conditions, liquidity, and counterparty risks, and provide data-driven feedback to the Trader Agent. 
Suggest mitigation strategies like moderate stop-loss orders and portfolio diversification. 
You operate as a stabilizing force in the team, seeking sustainable performance. 
Use the ReAct framework to reason through market events and respond with well-measured risk management actions.
"""
llm = ChatOpenAI(model='gpt-4o-mini')
neutral_risk_manager_tools = ["arxiv", "ddg-search", "wikipedia"]
neutral_risk_manager = DialogueAgentWithTools(
    name="Neutral Risk Manager",
    system_message=SystemMessage(content=neutral_risk_manager_system_message ),
    model=llm,
    tool_names=neutral_risk_manager_tools
)
