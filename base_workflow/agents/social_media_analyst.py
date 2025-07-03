from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

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

class SocialMediaAnalystSignal(BaseModel):
    """
    Container for the social media analyst output signal.
    """
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str

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


def social_media_analyst_agent(state: AgentState):
    """Analyzes sentiment signals and generates trading signals for multiple slugs."""
    """The initiative lies with the sentiment analyst, 
    who decides to generate reports and gives the final trading signals."""
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
    
        # 主要观察balance_total, 并且观察positive_total 和 negative_total的变化趋势并作为参考。
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


        # 看看这部分是不是有在不断增加
        # 都是从这一刻往前算的

        progress.update_status("sentiment_analyst_agent", slug, "social_volume_analysing")
        social_volume_total_change_7d = get_social_volume_total_change_7d(
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
        print(social_volume_total_change_30d)
        social_volume_total_change_1d = get_social_volume_total_change_1d(
            slug = 'social_volume_total_change_1d' + slug,
            end_date=end_date,
            start_date=start_date,
        ) 
        
        # 用多个时间窗口（例如 1 日、3 日、7 日）分别计算情绪 neg pos momentum
        # 任意两个pos_mom > 0 就认为是正面情绪，否则负面情绪。
        # Can be used as an auxiliary sentiment analysis tool， 
        # calculate also the momentum of this value to show the trend
        sentiment_weighted_data = get_sentiment_weighted_total(
            slug = 'social_sentiment_weighted_total' + slug,
            end_date=end_date,
            start_date=start_date,
        )
        # check 
        # sentiment_weighted_signals = {
        #     "signal": "positive",
        #     "momentum": sentiment_weighted_data.momentum
        # }
        # sentiment_weighted_signals = {
        #     "signal": "negative",
        #     "momentum": sentiment_weighted_data.momentum
        # }
        # sentiment_weighted_signals = {
        #     "signal": "neutral",
        #     "momentum": sentiment_weighted_data.momentum
        # }

        progress.update_status("sentiment_analyst_agent", slug, "fear_and_greed_index_analysing")
        # fear_and_greed_index now only support today's data.
        fear_and_greed_index = get_fear_and_greed_index(target_date = end_date)
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
        
        social_media_analysis_data[slug] = {
        "signal": signal,
        "score": total_score,
        "max_score": max_possible_score,
        "growth_analysis": growth_analysis,
        "valuation_analysis": valuation_analysis,
        "fundamentals_analysis": fundamentals_analysis,
        "sentiment_analysis": sentiment_analysis,
        "insider_activity": insider_activity,
        }

        progress.update_status("peter_lynch_agent", slug, "social_media_analysis")
        social_media_analysis_output = social_media_analysis_output(
            slug=slug,
            analysis_data=social_media_analysis_data[slug],
            model_name=state["metadata"]["model_name"],
            model_provider=state["metadata"]["model_provider"],
        )

        social_media_analysis[slug] = {
            "signal": lynch_output.signal,
            "confidence": lynch_output.confidence,
            "reasoning": lynch_output.reasoning,
        }

        progress.update_status("sentiment_agent", slug, "Done")
    
    # Create the technical analyst message
    message = HumanMessage(
        content=json.dumps(sentiment_analysis),
        name="sentiment_analyst_agent",
    )

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(lynch_analysis, "Peter Lynch Agent")

    # Save signals to state
    state["data"]["analyst_signals"]["peter_lynch_agent"] = lynch_analysis

    return {"messages": [message], "data": state["data"]}



def generate_social_media_analyst_output(
    slug: str,
    analysis_data: dict[str, any],
    model_name: str,
    model_provider: str,
):
    """
    Generates a final JSON report of social_media_analyst.
    """
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Peter Lynch AI agent. You make investment decisions based on Peter Lynch's well-known principles:
                
                1. Invest in What You Know: Emphasize understandable businesses, possibly discovered in everyday life.
                2. Growth at a Reasonable Price (GARP): Rely on the PEG ratio as a prime metric.
                3. Look for 'Ten-Baggers': Companies capable of growing earnings and share price substantially.
                4. Steady Growth: Prefer consistent revenue/earnings expansion, less concern about short-term noise.
                5. Avoid High Debt: Watch for dangerous leverage.
                6. Management & Story: A good 'story' behind the stock, but not overhyped or too complex.
                
                When you provide your reasoning, do it in Peter Lynch's voice:
                - Cite the PEG ratio
                - Mention 'ten-bagger' potential if applicable
                - Refer to personal or anecdotal observations (e.g., "If my kids love the product...")
                - Use practical, folksy language
                - Provide key positives and negatives
                - Conclude with a clear stance (bullish, bearish, or neutral)
                
                Return your final output strictly in JSON with the fields:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": 0 to 100,
                  "reasoning": "string"
                }}
                """,
            ),
            (
                "human",
                """Based on the following analysis data for {ticker}, produce your Peter Lynch–style investment signal.

                Analysis Data:
                {analysis_data}

                Return only valid JSON with "signal", "confidence", and "reasoning".
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return SocialMediaAnalystSignal(
            signal="neutral",
            confidence=0.0,
            reasoning="Error in analysis; defaulting to neutral"
        )

    return call_llm(
        prompt=prompt,
        model_name=model_name,
        model_provider=model_provider,
        pydantic_model=SocialMediaAnalystSignal,
        agent_name="peter_lynch_agent",
        default_factory=create_default_signal,
    )


if __name__ == "__main__":
    # At the end only need the end_date, start_date should be two weeks or one month before the end_date
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
    result = social_media_analyst_agent(test_state)
    print(result)