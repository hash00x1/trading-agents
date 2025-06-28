from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
import pandas as pd
import numpy as np
import json
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent


##### Financial News Sentiment Agent #####
### Maybe only for test use, later combine with the social_media_analyst.py ###

news_analyst_system_message = """
You are a News Analyst Agent in a multi-agent financial analysis system.

Your role is to investigate and summarize relevant macroeconomic, geopolitical, and market-moving news from the past week. Your objective is to deliver actionable and concise insights that may impact trading decisions.

## Tasks:
- Review and analyze news from multiple sources, such as:
  - Financial news portals (e.g., Bloomberg, Reuters, Google News)
  - Aggregated global headlines from trusted APIs
- Identify key macroeconomic themes: inflation, interest rates, employment, GDP, central bank policy, etc.
- Highlight geopolitical events affecting global markets.
- Detect sector-specific or company-specific breaking news.
- Filter noise and emphasize only news with potential market impact.

## Output Format (structured + readable):
Provide a Markdown report including:
- Summary of major themes
- Headline events with short explanations
- Sector/company-specific news (if any)
- Markdown table summarizing:
  - Date | Event | Market Implication | Source

## Constraints:
- Avoid repeating generic phrases (e.g., "markets were mixed")
- Focus only on factual, news-driven insights
- Don't include price data or technical indicators
- Write like a professional analyst briefing a trading team
"""

from langchain_openai import ChatOpenAI
from langgraph.graph import create_react_agent

llm = ChatOpenAI(model='gpt-4o-mini')
news_analyst_tools = [toolkit.get_reddit_news, toolkit.get_google_news]

news_analyst = create_react_agent(
    llm,
    tools=news_analyst_tools,
    state_modifier=news_analyst_system_message,
)

# Set here directly into an agent.
# Combine the tools of news crawler.
# initialized with the openai_news_crawler.

# # FinBERT (yiyanghkust) based for financial news#
# def news_sentiment_agent(state: AgentState):
#     """Analyzes market sentiment and generates trading signals for multiple tickers."""
#     # data = state.get("data", {})
#     # end_date = data.get("end_date")
#     # tickers = data.get("tickers")
#     data = state["data"]
#     start_date = data["start_date"]
#     end_date = data["end_date"]
#     interval = data["time_interval"]
#     tickers = data["tickers"]

#     # Initialize news sentiment analysis for each ticker
#     news_sentiment_analysis = {}

#     for ticker in tickers:
#         # Get the company news
#         company_news = get_company_news(ticker, end_date, limit=100)

#         # Get the sentiment from the company news
#         sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
#         news_signals = np.where(sentiment == "negative", "bearish", 
#                               np.where(sentiment == "positive", "bullish", "neutral")).tolist()
        
#         progress.update_status("sentiment_agent", ticker, "Combining signals")
#         # Combine signals from both sources with weights
#         insider_weight = 0.3
#         news_weight = 0.7
        
#         # Calculate weighted signal counts
#         bullish_signals = (
#             insider_signals.count("bullish") * insider_weight +
#             news_signals.count("bullish") * news_weight
#         )
#         bearish_signals = (
#             insider_signals.count("bearish") * insider_weight +
#             news_signals.count("bearish") * news_weight
#         )

#         if bullish_signals > bearish_signals:
#             overall_signal = "bullish"
#         elif bearish_signals > bullish_signals:
#             overall_signal = "bearish"
#         else:
#             overall_signal = "neutral"

#         # Calculate confidence level based on the weighted proportion
#         total_weighted_signals = len(insider_signals) * insider_weight + len(news_signals) * news_weight
#         confidence = 0  # Default confidence when there are no signals
#         if total_weighted_signals > 0:
#             confidence = round(max(bullish_signals, bearish_signals) / total_weighted_signals, 2) * 100
#         reasoning = f"Weighted Bullish signals: {bullish_signals:.1f}, Weighted Bearish signals: {bearish_signals:.1f}"

#         news_sentiment_analysis[ticker] = {
#             "signal": overall_signal,
#             "confidence": confidence,
#             "reasoning": reasoning,
#         }

#         progress.update_status("sentiment_agent", ticker, "Done")

#     # Create the sentiment message
#     message = HumanMessage(
#         content=json.dumps(news_sentiment_analysis),
#         name="sentiment_agent",
#     )

#     # Print the reasoning if the flag is set
#     if state["metadata"]["show_reasoning"]:
#         show_agent_reasoning(news_sentiment_analysis, "Sentiment Analysis Agent")

#     # Add the signal to the analyst_signals list
#     state["data"]["analyst_signals"]["sentiment_agent"] = news_sentiment_analysis

#     return {
#         "messages": [message],
#         "data": data,
#     }


if __name__ == "__main__":
    # Test the technical analyst agent with dummy data
    test_state = AgentState(
        messages=[],
        data={
            "tickers": ["ohlcv/bitcoin" ],
            "start_date": "2023-01-01",
            "end_date": "2023-10-01",
            "time_interval": "1d",
        },
        metadata={"show_reasoning": False},
    )

    # Run the agent
    result = news_sentiment_agent(test_state)
    print(result)