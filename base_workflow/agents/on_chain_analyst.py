from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import json

from base_workflow.tools.api_price import get_financial_metrics

#### On-Chain Data Analyst Agent #####
# Book: do Fundamentals Drive Cryptocurrency Prices?
# Analyzes on-chain metrics like active addresses, transaction volume, whale behavior.
# computing power
# Network Size: Measured by the number of active users or addresses, indicating adoption and utility.
# Generates a trading signal (bullish, bearish, neutral) for each cryptocurrency
# Provides human-readable reasoning and a confidence score

def on_chain_data_analyst_agent(state: AgentState):
    """Analyzes on-chain data using Santiment and generates trading signals."""
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    onchain_analysis = {}

    for ticker in tickers:
        progress.update_status("onchain_agent", ticker, "Fetching on-chain metrics")

        signals = []
        reasoning = {}

        # 活跃地址分析（活跃用户越多越 bullish）daily_active_addresses  liquity_active_addresses
        active_addresses = metrics.get("active_addresses")
        if active_addresses and active_addresses > metrics.get("active_avg_30d", 0) * 1.2:
            signals.append("bullish")
        elif active_addresses and active_addresses < metrics.get("active_avg_30d", 0) * 0.8:
            signals.append("bearish")
        else:
            signals.append("neutral")
        reasoning["active_addresses_signal"] = {
            "signal": signals[-1],
            "details": f"Active: {active_addresses}, 30D Avg: {metrics.get('active_avg_30d')}",
        }

        # # 2. 交易量分析
        # tx_volume = metrics.get("transaction_volume")
        # if tx_volume and tx_volume > metrics.get("volume_avg_30d", 0) * 1.5:
        #     signals.append("bullish")
        # elif tx_volume and tx_volume < metrics.get("volume_avg_30d", 0) * 0.7:
        #     signals.append("bearish")
        # else:
        #     signals.append("neutral")
        # reasoning["tx_volume_signal"] = {
        #     "signal": signals[-1],
        #     "details": f"Tx Volume: {tx_volume}, 30D Avg: {metrics.get('volume_avg_30d')}",
        # }

        # 3. 鲸鱼地址行为（增加持仓通常 bullish）
        whale_balance_change = metrics.get("whale_balance_change")
        if whale_balance_change and whale_balance_change > 0:
            signals.append("bullish")
        elif whale_balance_change and whale_balance_change < 0:
            signals.append("bearish")
        else:
            signals.append("neutral")
        reasoning["whale_signal"] = {
            "signal": signals[-1],
            "details": f"Whale Balance Change: {whale_balance_change}",
        }

        progress.update_status("onchain_agent", ticker, "Calculating final signal")
        bullish_signals = signals.count("bullish")
        bearish_signals = signals.count("bearish")

        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        confidence = round(max(bullish_signals, bearish_signals) / len(signals), 2) * 100

        onchain_analysis[ticker] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("onchain_agent", ticker, "Done")

    message = HumanMessage(
        content=json.dumps(onchain_analysis),
        name="onchain_data_analyst_agent",
    )

    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(onchain_analysis, "On-Chain Data Analyst Agent")

    state["data"]["analyst_signals"]["onchain_data_analyst_agent"] = onchain_analysis

    return {
        "messages": [message],
        "data": data,
    }
