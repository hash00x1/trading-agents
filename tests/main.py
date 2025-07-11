import sys
import argparse
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph
from colorama import Fore, Back, Style, init
import questionary
from base_workflow.agents import (
    technical_analyst,
    news_analyst,
    on_chain_analyst,
    social_media_analyst,
    bullish_researcher,
    bearish_researcher,
    research_manager,
    risk_manager,
    portfolio_manager,
    DialogueAgent,
    DialogueSimulatorAgent,
    DialogueAgentWithTools
)
from base_workflow.graph.state import AgentState

from base_workflow.utils.progress import progress

import argparse
import json

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)


def parse_response(response):
    """Parses a JSON string and returns a dictionary."""
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}\nResponse: {repr(response)}")
        return None
    except TypeError as e:
        print(f"Invalid response type (expected string, got {type(response).__name__}): {e}")
        return None
    except Exception as e:
        print(f"Unexpected error while parsing response: {e}\nResponse: {repr(response)}")
        return None



##### Run the Crypto Agents Team #####
def run(
    slugs: list[str],
    start_date: str,
    end_date: str,
    time_interval: str = "4h",
    # portfolio: dict,
    show_reasoning: bool = False,
):
    # Start progress tracking
    progress.start()

    try:
        # Create a new workflow if analysts are customized
        agent = app

        final_state = agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content="Make trading decisions based on the provided data.",
                    )
                ],
                "data": {
                    "slugs": slugs,
                    # "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "time_interval": time_interval,
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    # "model_name": model_name,
                    # "model_provider": model_provider,
                },
            },
        )
        return {
            "messages": final_state["messages"],
            "data": final_state["data"],
        }
    finally:
        # Stop progress tracking
        progress.stop()


def start(state: AgentState):
    """Initialize the workflow with the input message."""
    return state


def create_workflow(selected_analysts=None):
    """Create the workflow with selected analysts."""
    workflow = StateGraph(AgentState)
    workflow.add_node("start_node", start)
    workflow.add_node("technical_analyst", technical_analyst)
    workflow.add_node("social_media_analyst", social_media_analyst)
    workflow.add_node("news_analyst", news_analyst)
    workflow.add_node("on_chain_analyst", on_chain_analyst)
    workflow.add_node("research_manager", research_manager)
    workflow.add_node("risk_manager", risk_manager)
    #workflow.add_node("portfolio_manager", portfolio_manager)

    # Define the workflow edges of research team
    workflow.set_entry_point("technical_analyst")
    workflow.add_edge("technical_analyst", "social_media_analyst")
    workflow.add_edge("social_media_analyst", "news_analyst")
    workflow.add_edge("news_analyst", "on_chain_analyst")
    workflow.add_edge("on_chain_analyst", "research_manager")
    workflow.add_edge("research_manager", "risk_manager")
    workflow.add_edge( "risk_manager", END)
    # workflow.add_edge("portfolio_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


if __name__ == "__main__":

    test_state = AgentState(
        messages=[],
        data={
            "slugs": ["bitcoin" ],
            "start_date": "2024-06-07",
            "end_date": "2024-08-08",
            "time_interval": "4h",
        },
        metadata={"show_reasoning": False},
    )

    # Create the workflow with selected analysts
    workflow = create_workflow()
    app = workflow.compile()

    # Run the hedge fund
    result = run(
        slugs=test_state["data"]["slugs"],
        start_date=test_state["data"]["start_date"],
        end_date=test_state["data"]["end_date"],
        time_interval=test_state["data"]["time_interval"],
        # portfolio=portfolio,
        show_reasoning=test_state["metadata"].get("show_reasoning", False),
    )
    print(result)
