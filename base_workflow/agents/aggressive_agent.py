from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from base_workflow.tools import read_document, python_repl_tool

aggressive_agent_system_message = ""
aggressive_agent_tools = []
llm = ChatOpenAI(model="gpt-4o")

aggressive_agent = create_react_agent(
	llm,
	tools=aggressive_agent_tools,
	state_modifier=aggressive_agent_system_message,
)
