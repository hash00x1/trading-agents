from calendar import c
from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent
from langchain_core.messages import SystemMessage
from base_workflow.graph.state import AgentState



conservative_risk_manager_system_message = """
You are the Conservative Risk manager, focused on capital preservation and financial stability. 
Your priority is to avoid adverse market outcomes by minimizing risk exposure, even at the cost of potential gains. 
You carefully evaluate volatility, liquidity, and systemic risks, and advocate for conservative strategies—such as diversification across low-risk assets and strict stop-loss thresholds. 
Provide clear warnings to the Trader Agent when market conditions become unfavorable or when strategies exceed conservative limits. 
Rely on the ReAct prompting approach to proactively detect risks and recommend protective actions. 
You ensure the firm’s long-term sustainability and compliance.
"""
llm = ChatOpenAI(model="gpt-4o")

def conservative_risk_manager(state: AgentState):
    agent = DialogueAgent(
        name="Conservative Risk Manager",
        system_message=SystemMessage(content=conservative_risk_manager_system_message ),
        model=llm,
        state=state
    )
    
    message_content = agent.send()

    return agent.state