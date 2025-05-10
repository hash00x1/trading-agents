from calendar import c
from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgentWithTools
from langchain_core.messages import SystemMessage



conservative_risk_manager_system_message = """
You are the Conservative Risk manager, focused on capital preservation and financial stability. 
Your priority is to avoid adverse market outcomes by minimizing risk exposure, even at the cost of potential gains. 
You carefully evaluate volatility, liquidity, and systemic risks, and advocate for conservative strategies—such as diversification across low-risk assets and strict stop-loss thresholds. 
Provide clear warnings to the Trader Agent when market conditions become unfavorable or when strategies exceed conservative limits. 
Rely on the ReAct prompting approach to proactively detect risks and recommend protective actions. 
You ensure the firm’s long-term sustainability and compliance.
"""
conservative_risk_manager_tools = ["arxiv", "ddg-search", "wikipedia"]
llm = ChatOpenAI(model="gpt-4o")

conservative_risk_manager = DialogueAgentWithTools(
    name="Conservative Risk Manager",
    system_message=SystemMessage(content=conservative_risk_manager_system_message ),
    model=llm,
    tool_names=conservative_risk_manager_tools
)
