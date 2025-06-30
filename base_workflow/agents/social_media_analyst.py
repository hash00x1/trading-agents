from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import json

from base_workflow.tools import (get_sentiment_positive_total,
                                           get_sentiment_negative_total,
                                           get_sentiment_balance_total)


##### Social Media Sentiment Agent #####
# the sentiment API from santiment
# sentiment_weighted_total: An improved version of the Sentiment Balance that adjusts the values by considering the number of mentions, 
#                            standardizing data to make diverse asset sentiments comparable.
# sentiment_negative_total, sentiment_positive_total: Shows how many mentions of a term/asset are expressed in a positive/negative manner.
# sentiment_balance_total:  The difference between Positive Sentiment and Negative Sentiment
# social_volume_total, 
# social_volume_total_change_30d,
# social_volume_total_change_7d, 
# social_volume_total_change_1d,
# fear and greed index 
##########################################
# Social Volume analysis
# mainly use momentum indicates the changes in social media activity around a cryptocurrency
# sentiment_weighted_total: 看看怎么用

# sentiment_positive_total: 计算momentum
# sentiment_negative_total: 计算momentum,两个看看哪个的增长速度快
# sentiment_balance_total: 看看是正面高还是负面高
# social_volume: 看看是否有人持续关注，并且关注的人数在不断增长

# fear_and_greed_index:
# 0-100, 0-50是恐惧，50-100是贪婪
# 0-25是极度恐惧，25-50是恐惧，50-75是贪婪，75-100是极度
##############################################################################################################


def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals for multiple slugs."""
    # data = state.get("data", {})
    # end_date = data.get("end_date")
    # tickers = data.get("tickers")
    slugs = ["bitcoin" ] # later add this to the main whole slug name used in santiment API
    end_date = "2025-05-08"
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(weeks=2)
    start_date = start_dt.date().isoformat()

    # Initialize sentiment analysis for each slug
    sentiment_analysis = {}

    for slug in slugs:
        progress.update_status("social_media_sentiment_agent", slug, "Fetching Sentiment Scores from Telegram, Twitter, and YouTube")

        
        progress.update_status("social_media_sentiment_agent", slug, "Analyzing Sentiment Scores")
        # Calculate the sentiment score of the news.


        # Get the signals from the insider trades
        transaction_shares = pd.Series([t.transaction_shares for t in insider_trades]).dropna()
        insider_signals = np.where(transaction_shares < 0, "bearish", "bullish").tolist()

        progress.update_status("social_media_sentiment_agent", slug, "Fetching company news")

        # Get the sentiment from the company news
        sentiment = pd.Series([n.sentiment for n in company_news]).dropna()
        news_signals = np.where(sentiment == "negative", "bearish", 
                              np.where(sentiment == "positive", "bullish", "neutral")).tolist()
        
        progress.update_status("sentiment_agent", slug, "Combining signals")
        
        # Calculate weighted signal counts
        bullish_signals = (
            news_signals.count("bullish") * news_weight
        )
        bearish_signals = (

            news_signals.count("bearish") * news_weight
        )
        # Strategy:
        # if two of the three sources are bullish, then the overall signal is bullish.
        # if two of the three sources are bearish, then the overall signal is bearish.
        if bullish_signals > bearish_signals:
            overall_signal = "bullish"
        elif bearish_signals > bullish_signals:
            overall_signal = "bearish"
        else:
            overall_signal = "neutral"

        # Calculate confidence level
        total_weighted_signals = len(insider_signals) * insider_weight + len(news_signals) * news_weight
        confidence = 0  # Default confidence when there are no signals
        if total_weighted_signals > 0:
            confidence = round(max(bullish_signals, bearish_signals) / total_weighted_signals, 2) * 100
        reasoning = f"Weighted Bullish signals: {bullish_signals:.1f}, Weighted Bearish signals: {bearish_signals:.1f}"

        sentiment_analysis[slug] = {
            "signal": overall_signal,
            "confidence": confidence,
            "reasoning": reasoning,
        }

        progress.update_status("sentiment_agent", slug, "Done")

    # Create the sentiment message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_agent",
    )

    # Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # Add the signal to the analyst_signals list
    state["data"]["analyst_signals"]["sentiment_agent"] = sentiment_analysis
    # Check here how was it done in the original work.
    return {
        "messages": [message],
        "data": data,
    }
