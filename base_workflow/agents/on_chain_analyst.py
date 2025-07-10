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
import pandas as pd
import numpy as np
from scipy.stats import linregress

from base_workflow.tools import get_daily_active_addresses

#### On-Chain Data Analyst Agent #####
# Book: do Fundamentals Drive Cryptocurrency Prices?
# Analyzes on-chain metrics like active addresses, transaction volume, whale behavior.
# computing power
# Network Size: Measured by the number of active users or addresses, indicating adoption and utility.
# Generates a trading signal (bullish, bearish, neutral) for each cryptocurrency
# Provides human-readable reasoning and a confidence score
# based on https://medium.com/coinmonks/a-beginners-guide-to-on-chain-analysis-1f2689efd9aa

def on_chain_analyst(state: AgentState):
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
    on_chain_data = {}
    on_chain_analysis = {}

    for slug in slugs:
        progress.update_status("on_chain_analyst", slug, "Fetching Network metrics")

        # 1.  Network Activity : 'daily_active_address', transation volume

        _, daily_active_addresses = get_daily_active_addresses(
            slug,
            end_date=str(end_date),
            start_date=start_date
        )
        daily_active_addresses_signal = analyse_daa_trend(daily_active_addresses)
        on_chain_data[slug] = {
            "daily_active_addresses_signal" : daily_active_addresses_signal,
        }


        
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
        progress.update_status("on_chain_analyst", slug, "Analysing numerical data.")
        on_chain_analyst_system_message = """
        You are an on chain data analyst, 
        You play as analyst assistant in a multi-agent system, focused on gathering and analysing on chain data for cryptos.
        For your reference, the current date is {date}, we are looking at {cryptos}.

        Your main task:
        - Your role is to analyze, and summarize on-chain activity for the given cryptocurrencies.
        - Provide accurate, reliable, and actionable insights that support trading decisions and write into a report.

        You analysis is based on this data: {on_chain_data_signal_set}

        - DAA (Daily Active Addresses) Analysis:
            - Use short-term EMA to classify DAA trend (upward/downward).
            - Apply MACD crossover to detect momentum shifts.
            - Compute slope to measure trend strength.

        Your output must consist of three parts:

        ---

        ### Part 1: **News Sentiment Report**
        - A structured summary of:
            - Key on-chain metrics and their recent changes
            - Interpretation of patterns (e.g., accumulation, distribution, spikes)
            - Potential implications for short-term market movement

        ---

        ### Part 2: **Trading Signal**
        - Based on your on-chain analysis, provide a clear trading recommendation:
            - Format: `Trading Signal: **Buy** / **Hold** / **Sell**`
            - No explanation should follow—just the signal.

        ---

        ### Part 3: **Confidence Level** 
        - Provide a confidence level for your signal as a float number.
        - The format must be: `Confidence Level: <float number>`
        - This number represents how confident you are in your signal, where:
            - 1 indicates extremely positive sentiment
            - 0.5 to 0.9 indicates positive sentiment
            - 0.1 to 0.4 indicates slightly positive sentiment 
            - 0 indicates neutral sentiment 
            - -0.1 to -0.4 indicates slightly negative sentiment
            - -0.5 to -0.9 indicates negative sentiment
            - -1 indicates extremely negative sentiment
        - Please return only the float number, no explanation.

        ---
        Keep your analysis concise, data-driven, and focused on actionable metrics. 
        Do not include any unrelated commentary or sections.
        """.format(date=end_date, cryptos=slug, on_chain_data_signal_set=on_chain_data)

        # Just invoke the message is enough here.
        analyst_message = llm.invoke([HumanMessage(content=on_chain_analyst_system_message)])
        content = str(analyst_message.content)
        print(content)
        
        # Extract Social Media Sentiment Report
        part1_match = re.search(
            r"### Part 1:\s+\*\*Social Media\s+Sentiment\s+Report\*\*\s*\n+(.*?)(?=\n+---\n+\n+### Part 2:)", 
            content, 
            re.DOTALL
            )
        on_chain_report = part1_match.group(1).strip() if part1_match else None
        # print(news_report)

        # Extract Trading Signal
        part2_match = re.search(
            r"### Part 2: \*\*Trading Signal\*\*.*?Trading Signal: \*\*(Buy|Hold|Sell)\*\*", 
            content, re.DOTALL
            )
        trading_signal = part2_match.group(1) if part2_match else None
        # print(trading_signal)
        
        # Extract Confidence Level
        part3_match = re.search(
            r"### Part 3: \*\*Confidence Level\*\*.*?Confidence Level: ([\-\d\.]+)",
            content,
            re.DOTALL
        )
        confidence_level = float(part3_match.group(1)) if part3_match else None
        # print(confidence_level)

        on_chain_analysis[slug] = {
            "signal": trading_signal,
            "confidence": confidence_level,
            "report": on_chain_report,
        }
        progress.update_status("on_chain_analyst", slug, "Done")    

    message = HumanMessage(
        content=json.dumps(on_chain_analysis),
        name="on_chain_analyst",
    )

    return {
        "messages": [message],
        "data": data,
    }




def analyse_daa_trend(df: pd.DataFrame):
    """
    Advanced analysis of DAA (Daily Active Addresses):
    - Short-term EMA-based trend classification.
    - MACD crossover momentum signal.
    - Additional slope metric for trend strength.
    
    Returns:
        dict:
            {
                'trend': 'increasing' | 'decreasing' | 'stable',
                'macd_signal': 'bullish' | 'bearish' | 'neutral',
                'metrics': {
                    'ema_slope': float,
                    'macd_current': float,
                    'macd_signal_current': float,
                    'macd_hist_current': float
                },
                'explanation': str
            }
    """
    if df.empty or 'value' not in df.columns:
        return {
            "trend": "unknown",
            "macd_signal": "unknown",
            "metrics": {},
            "explanation": "DAA data is empty or invalid."
        }

    # Compute short-term EMA
    bars_2d = 3 * 6  # ~2 days for 8h bars
    df['ema_short'] = df['value'].ewm(span=bars_2d, adjust=False).mean()
    recent_ema = df['ema_short'].tail(bars_2d)

    # Compute slope of recent EMA for smoother trend signal
    x = np.arange(len(recent_ema))
    y = recent_ema.values
    slope, _, _, _, _ = linregress(x, y)
    ema_slope = float(slope)

    # Trend classification with slope + count logic
    inc_count = (recent_ema.diff() > 0).sum()
    dec_count = (recent_ema.diff() < 0).sum()
    
    if ema_slope > 0 and inc_count > bars_2d / 2:
        trend = "increasing"
    elif ema_slope < 0 and dec_count > bars_2d / 2:
        trend = "decreasing"
    else:
        trend = "stable"

    # MACD computation
    ema_12 = df['value'].ewm(span=12, adjust=False).mean()
    ema_26 = df['value'].ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_sig = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_sig

    macd_now = macd.iloc[-1]
    sig_now = macd_sig.iloc[-1]
    hist_now = macd_hist.iloc[-1]
    macd_prev = macd.iloc[-2]
    sig_prev = macd_sig.iloc[-2]

    if macd_prev < sig_prev and macd_now > sig_now:
        macd_signal = 'bullish'
    elif macd_prev > sig_prev and macd_now < sig_now:
        macd_signal = 'bearish'
    else:
        macd_signal = 'neutral'

    return {
        "trend": trend,
        "macd_signal": macd_signal,
        "metrics": {
            "ema_slope": ema_slope,
            "macd_current": macd_now,
            "macd_signal_current": sig_now,
            "macd_hist_current": hist_now
        }
    }

if __name__ == "__main__":

    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(AgentState)
    workflow.add_node("on_chain_analyst", on_chain_analyst)
    workflow.set_entry_point("on_chain_analyst")
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