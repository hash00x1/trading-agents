from langchain_core.messages import HumanMessage
from graph.state import AgentState, show_agent_reasoning
from utils.progress import progress
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import json

from base_workflow.tools.api_price import (get_twitter_positive_sentiment_score, 
                       get_twitter_negative_sentiment_score, 
                       get_reddit_negative_sentiment_score, 
                       get_reddit_positive_sentiment_score,
                       get_telegram_positive_sentiment_score,
                       get_telegram_negative_sentiment_score,)


##### Social Media Sentiment Agent #####
# getting the sentiment scores of three main media Telegram, Twitter, Reddit from santiment API #
# Sentiment Analysis
# Calculate a weighted sentiment score (sentiment_score) by aggregating sentiment data from Telegram, Twitter, and YouTube
# Social Volume analysis
# combine the discussion volume (volume_score) from Telegram, Twitter, and YouTube. A higher discussion volume typically 
# indicates increased market interest in an asset, which could be a precursor to price fluctuations
# Trading SIgnal Generation
# based on the sentiment_score and volume_score, generate a trading signal (bullish, bearish, neutral)



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

        # Get the Sentiment Scores from Telegram, Twitter, and YouTube
        telegram_positive_sentiment_score = get_telegram_positive_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        telegram_negative_sentiment_score = get_telegram_negative_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        twitter_positive_sentiment_score = get_twitter_positive_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        twitter_negative_sentiment_score = get_twitter_negative_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        reddit_positive_sentiment_score = get_reddit_positive_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        reddit_negative_sentiment_score = get_reddit_negative_sentiment_score(slug=slug, start_date=start_date, end_date=end_date)
        # Calculate the sentiment score
        
        progress.update_status("social_media_sentiment_agent", slug, "Analyzing Sentiment Scores")
        # Calculate the sentiment score of the news.

        # Set the weights for each source to calculate the overall sentiment score
        social_media_weight = 0.4
        news_weight = 0.6


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
