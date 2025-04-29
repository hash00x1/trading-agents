from langgraph.graph import MessagesState
from pathlib import Path
from langchain.agents import tool
from langchain_experimental.utilities import PythonREPL
from typing import Annotated, List

class State(MessagesState):
    next: str

WORKING_DIRECTORY = Path("base_workflow/outputs")
WORKING_DIRECTORY.mkdir(parents=True, exist_ok=True)

@tool
def create_outline(
    points: Annotated[List[str], "List of main points or sections."],
    file_name: Annotated[str, "File path to save the outline."],
) -> Annotated[str, "Path of the saved outline file."]:
    """Create and save an outline."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        for i, point in enumerate(points):
            file.write(f"{i + 1}. {point}\n")
    return f"Outline saved to {file_name}"