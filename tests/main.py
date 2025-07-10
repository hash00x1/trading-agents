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
    aggressive_risk_manager,
    conservative_risk_manager,
    neutral_risk_manager,
    portfolio_manager,
    DialogueAgent,
    DialogueSimulatorAgent,
    DialogueAgentWithTools
)
from base_workflow.graph.state import AgentState

from base_workflow.utils.progress import progress

import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabulate import tabulate
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
                    "portfolio": portfolio,
                    "start_date": start_date,
                    "end_date": end_date,
                    "analyst_signals": {},
                },
                "metadata": {
                    "show_reasoning": show_reasoning,
                    # "model_name": model_name,
                    # "model_provider": model_provider,
                },
            },
        )

        return {
            "decisions": parse_response(final_state["messages"][-1].content),
            "analyst_signals": final_state["data"]["analyst_signals"],
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
    # workflow.add_node("research_manager", research_manager)
    # workflow.add_node("risk_managemer", risk_manager)
    #workflow.add_node("portfolio_managemer", portfolio_manager)

    # Define the workflow edges of research team
    workflow.set_entry_point("technical_analyst")
    workflow.add_edge("technical_analyst", "social_media_analyst")
    workflow.add_edge("social_media_analyst", "news_analyst")
    # workflow.add_edge("news_analyst", "on_chain_analyst")
    workflow.add_edge("on_chain_analyst", END)
    # workflow.add_edge("research_manager", END)
    # workflow.add_edge("portfolio_management_agent", END)

    workflow.set_entry_point("start_node")
    return workflow


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the crypto agent team")
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=100000.0,
        help="Initial cash position. Defaults to 100000.0)"
    )
    parser.add_argument("--slugs", type=str, required=True, help="Comma-separated list of stock slug symbols")
    # 1 months is enough for all the operations
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 1 months before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument(
        "--show-agent-graph", action="store_true", help="Show the agent graph"
    )
    # parser.add_argument(
    #     "--ollama", action="store_true", help="Use Ollama for local LLM inference"
    # )

    if len(sys.argv) == 1:
        sys.argv.extend(['--slugs', 'bitcoin'])

    args = parser.parse_args()

    # Parse slugs from comma-separated string
    slugs = [slug.strip() for slug in args.slugs.split(",")]

    # Create the workflow with selected analysts
    workflow = create_workflow()
    app = workflow.compile()

    # draw graph
    # file_path = "/Users/taizhang/Desktop/ai-hedge-fund/src/agent_graph.png"
    # save_graph_as_png(app, file_path)

    # Validate dates if provided
    if args.start_date:
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

    if args.end_date:
        try:
            datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")

    # Set the start and end dates
    end_date = args.end_date or datetime.now().strftime("%Y-%m-%d")
    if not args.start_date:
        # Calculate 3 months before end_date
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")
    else:
        start_date = args.start_date

    # Initialize portfolio with cash amount and stock positions
    portfolio = {
        "cash": args.initial_cash,  # Initial cash amount
        "positions": {
            slug: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this slug's short
            } for slug in slugs
        },
        "realized_gains": {
            slug: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            } for slug in slugs
        }
    }

    # Run the hedge fund
    result = run(
        slugs=slugs,
        start_date=start_date,
        end_date=end_date,
        # portfolio=portfolio,
        show_reasoning=args.show_reasoning,
    )
    print(result)
