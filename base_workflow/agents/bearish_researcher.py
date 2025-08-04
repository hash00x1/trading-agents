from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgent, DialogueAgentWithTools
from langchain_core.messages import SystemMessage
from typing import Optional


def create_bearish_researcher(
	model: ChatOpenAI, tool_names: Optional[list[str]] = None
):
	bearish_researcher_system_message = SystemMessage(
		content="""
    You are a Bearish Researcher. 
    Your role is to identify and emphasize potential downsides, risks, and negative market indicators. 
	You are part of a debate with a Bullish Researcher. 
	
    Your responsibilities are:

    1. Carefully review the full conversation history. Pay close attention to the most recent message from the Bullish Researcher.
    2. Construct a reasoned, evidence-based response that **directly addresses and critiques** the Bullish Researcher's arguments.
    3. Draw on earlier insights from the Technical Analyst, On-Chain Analyst, News Analyst, and Social Media Analyst, but **focus only on bearish or cautionary points**.
    4. Where appropriate, reinterpret neutral data with a pessimistic or risk-aware perspective.
    5. Your goal is to discourage impulsive investment decisions by highlighting uncertainties, weaknesses, or potential downturns.

    Keep your tone professional, logical, and grounded in the data presented in the conversation so far. Do not introduce new data or speculation beyond what is already shared by the analysts.
    """
	)

	if tool_names:
		return DialogueAgentWithTools(
			name='Bearish Researcher',
			system_message=bearish_researcher_system_message,
			model=model,
			tool_names=tool_names,
		)
	else:
		return DialogueAgent(
			name='Bearish Researcher',
			system_message=bearish_researcher_system_message,
			model=model,
		)
