from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import json
import re
from pydantic import BaseModel
from typing_extensions import Literal
from langgraph.graph import StateGraph
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pydantic import datetime_parse
from scipy.stats import linregress
from langchain_core.messages import HumanMessage


from base_workflow.tools import get_daily_active_addresses

#### On-Chain Data Analyst Agent #####
# Book: do Fundamentals Drive Cryptocurrency Prices?
# Analyzes on-chain metrics like active addresses, transaction volume, whale behavior.
# computing power
# Network Size: Measured by the number of active users or addresses, indicating adoption and utility.
# Generates a trading signal (bullish, bearish, neutral) for each cryptocurrency
# Provides human-readable reasoning and a confidence score
# based on https://medium.com/coinmonks/a-beginners-guide-to-on-chain-analysis-1f2689efd9aa

def on_chain_data_analyst(state: AgentState):
    """Analyzes on-chain data using Santiment and generates trading signals."""
    messages = state.get("messages", [])
    data = state.get("data", {})
    end_date_str = data.get("end_date")
    end_date = datetime.strptime(str(end_date_str), "%Y-%m-%d")
    start_date = end_date - timedelta(weeks=2)
    start_date = start_date.strftime("%Y-%m-%d")

    slugs = data.get("slugs", [])
    llm = ChatOpenAI(model='gpt-4o-mini')
    interval = data["time_interval"]

    onchain_analysis = {}

    for slug in slugs:
        progress.update_status("onchain_agent", slug, "Fetching on-chain metrics")

        # 1.  Network Activity : 'daily_active_address', transation volume

        _, daily_active_addresses = get_daily_active_addresses(
            slug,
            end_date=str(end_date),
            start_date=start_date, 
        )
        print(daily_active_addresses)


        
        # 'transaction_volume_change_1d', 'transaction_volume_change_30d', 'transaction_volume_change_7d', 'transaction_volume_profit_loss_ratio', 'transaction_volume'


        # 3. Market Sentiment: Whale analysis, exchange inflow, exchange outflow. 

        
        # whale_balance_change = metrics.get("whale_balance_change")
        # if whale_balance_change and whale_balance_change > 0:
        #     signals.append("bullish")
        # elif whale_balance_change and whale_balance_change < 0:
        #     signals.append("bearish")
        # else:
        #     signals.append("neutral")
        # reasoning["whale_signal"] = {
        #     "signal": signals[-1],
        #     "details": f"Whale Balance Change: {whale_balance_change}",
        # 

    # return {
    #     "messages": [message],
    #     "data": data,
    # }


if __name__ == "__main__":

    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(AgentState)
    workflow.add_node("on_chain_data_analyst", on_chain_data_analyst)
    workflow.set_entry_point("on_chain_data_analyst")
    research_graph = workflow.compile()

    # Initialize state with messages as a list
    initial_state = {
        "messages": [
            HumanMessage(content="Make trading decisions based on the provided data.")
            ]       
        ,
        "data": {
            "slugs": ["bitcoin"],
            "start_date": "2024-06-07",
            "end_date": "2024-08-08",
            "time_interval": "4h",
        },
        "metadata": {
            "request_id": "test-123",
            "timestamp": "2025-07-02T12:00:00Z"
        }
    }

    final_state = research_graph.invoke(initial_state)

    print(final_state)