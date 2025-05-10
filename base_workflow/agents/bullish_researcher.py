from langchain_openai import ChatOpenAI
from .debate_agent import DialogueAgentWithTools
from langchain_core.messages import SystemMessage

llm = ChatOpenAI(model="gpt-4o")
bullish_researcher_tools = ["arxiv", "ddg-search", "wikipedia"]
bullish_researcher_system_message = """
You are a Bullish Researcher. Your role is to highlight positive indicators, growth potential, and favorable market conditions. 
You advocate for investment opportunities by emphasizing high growth, strong fundamentals, and positive market trends. 
You should encourage others to initiate or continue positions in certain assets.
"""
bullish_researcher = DialogueAgentWithTools(
    name="Bullish Researcher",
    system_message=SystemMessage(content=bullish_researcher_system_message),
    model=llm,
    tool_names=bullish_researcher_tools
)
