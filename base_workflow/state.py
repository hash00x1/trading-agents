from typing import Annotated
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import (
	TypedDict,
)


class AgentState(TypedDict):
	messages: Annotated[list[AnyMessage], add_messages]
