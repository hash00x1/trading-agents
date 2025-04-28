from typing import Annotated
from langchain.agents import tool
from langgraph.errors import NodeInterrupt


@tool
def ask_user(
	question: Annotated[str, 'The question to ask to the user.'],
):
	"""Use this to sk the human user a question."""
	raise NodeInterrupt(f'ask user question: {question}')
