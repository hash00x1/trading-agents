from typing import Annotated
from langchain_core.tools import tool
from langgraph.graph import MessagesState
from pathlib import Path

class State(MessagesState):
    next: str

WORKING_DIRECTORY = Path("base_workflow/outputs")
WORKING_DIRECTORY.mkdir(parents=True, exist_ok=True)

@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> Annotated[str, "Path of the saved document file."]:
    """Create and save a text document."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.write(content)
    return f"Document saved to {file_name}"