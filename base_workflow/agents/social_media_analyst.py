from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress

from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import json

from base_workflow.tools import (
    get_sentiment_weighted_total,
    get_social_volume_total,
    get_social_volume_total_change_1d,
    get_social_volume_total_change_7d,
    get_social_volume_total_change_30d,
    get_sentiment_balance_total,
    get_sentiment_negative_total,
    get_sentiment_positive_total,
    get_fear_and_greed_index,
    )



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

##############################################################################################################


def sentiment_analyst_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals for multiple slugs."""
    # data = state.get("data", {})
    # end_date = data.get("end_date")
    # tickers = data.get("tickers")
    # slugs = ["bitcoin" ] # later add this to the main whole slug name used in santiment API
    # end_date = "2025-05-08"
    # end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    # start_dt = end_dt - timedelta(weeks=2)
    # start_date = start_dt.date().isoformat()
    # Change the start_data to be two weeks before the end_date
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    interval = data["time_interval"]
    slugs = data["tickers"]

    # Initialize sentiment analysis for each slug
    sentiment_analysis = {}

    for slug in slugs:
        progress.update_status("sentiment_analyst_agent", slug, "social_sentiment_analysing")

        sentiment_weighted_data = get_sentiment_weighted_total(
            slug = 'social_sentiment_weighted_total' + slug,
            end_date=end_date,
            start_date=start_date,
        )
        sentiment_balance_total = get_sentiment_balance_total(
            slug = 'social_sentiment_weighted_total' + slug,
            end_date=end_date,
            start_date=start_date,    
        )
        sentiment_negative_total = get_sentiment_negative_total(
            slug = 'social_sentiment_negative_total' + slug,
            end_date=end_date,
            start_date=start_date,
        )
        sentiment_positive_total = get_sentiment_positive_total(
            slug = 'social_sentiment_positive_total' + slug,
            end_date=end_date,
            start_date=start_date,
        )

        progress.update_status("sentiment_analyst_agent", slug, "social_volume_analysing")
        social_volume_total_change_7d = get_social_volume_total_change_1d(
            slug = 'social_volume_total_change_7d' + slug,
            end_date=end_date,
            start_date=start_date,
        )
        # print(social_volume_total_change_7d)
        social_volume_total_change_30d = get_social_volume_total_change_30d(
            slug = 'social_volume_total_change_30d' + slug,
            end_date=end_date,
            start_date=start_date,
        )
        social_volume_total_change_1d = get_social_volume_total_change_1d(
            slug = 'social_volume_total_change_1d' + slug,
            end_date=end_date,
            start_date=start_date,
        )

        progress.update_status("sentiment_analyst_agent", slug, "fear_and_greed_index_analysing")
        # fear_and_greed_index now only support today's data.
        fear_and_greed_index = get_fear_and_greed_index()
        fear_and_greed_signals_confidence = fear_and_greed_index.value          
        fear_and_greed_signals_classification = fear_and_greed_index.classification
        if fear_and_greed_signals_classification == "fear":
            fear_and_greed_signals = {
                "signal": "fear",
                "confidence": fear_and_greed_signals_confidence,
            }
        elif fear_and_greed_signals_classification == "greed":  
            fear_and_greed_signals = {
                "signal": "greed",
                "confidence": fear_and_greed_signals_confidence,
            }
        else:
            fear_and_greed_signals = {
                "signal": "neutral",
                "confidence": fear_and_greed_signals_confidence,
            }


        




        sentiment_analysis[slug] = {
            # "signal": overall_signal,
            # "confidence": confidence,
            # "strategy_signals": {
            #     "social_sentiment_analysis": {
            #         "signal": social_sentiment_signals["signal"],
            #         "confidence": round(social_sentiment_signals["confidence"] * 100),
            #     },
            #     "social_volume_analysis": {
            #         "signal": social_volume_signals["signal"],
            #         "confidence": round(social_volume_signals["confidence"] * 100),
            #     },
                "fear_and_greed_index": {
                    "signal": fear_and_greed_signals["signal"],
                    "index": fear_and_greed_signals["confidence"]
                }
            }
        

        progress.update_status("sentiment_agent", slug, "Done")


    
    # Create the technical analyst message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_analyst_agent",
    )


    # Print the reasoning if the flag is set
    # if state["metadata"]["show_reasoning"]:
    #     show_agent_reasoning(sentiment_analysis, "Sentiment Analysis Agent")

    # Add the signal to the analyst_signals list
    # state["data"]["analyst_signals"]["sentiment_agent"] = sentiment_analysis
    # Check here how was it done in the original work.
    return {
        "messages": [message],
        "data": data,
    }


if __name__ == "__main__":
    test_state = AgentState(
        messages=[],
        data={
            "tickers": ["bitcoin"],
            "start_date": "2024-06-07",
            "end_date": "2024-08-08",
            "time_interval": "4h",
        },
        metadata={"show_reasoning": False},
    )

    # Run the agent
    result = sentiment_analyst_agent(test_state)
    print(result)