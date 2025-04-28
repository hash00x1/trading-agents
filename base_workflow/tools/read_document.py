from langchain_core.tools import tool
from langgraph.graph import MessagesState
from pathlib import Path
from typing import Optional, Annotated
from pathlib import Path

class State(MessagesState):
    next: str

WORKING_DIRECTORY = Path("base_workflow/outputs")
WORKING_DIRECTORY.mkdir(parents=True, exist_ok=True)

@tool
def read_document(
    file_name: Annotated[str, "File path to read the document from."],
    start: Annotated[Optional[int], "The start line. Default is 0"] = None,
    end: Annotated[Optional[int], "The end line. Default is None"] = None,
) -> str:
    """Read the specified document."""
    with (WORKING_DIRECTORY / file_name).open("r") as file:
        lines = file.readlines()
    if start is not None:
        start = 0
    return "\n".join(lines[start:end])