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
    report: str

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


def social_media_analyst(state: AgentState):
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
    messages = state.get("messages", [])
    data = state.get("data", {})
    end_date = data.get("end_date")
    slugs = data.get("slugs", [])
    llm = ChatOpenAI(model='gpt-4o-mini')
    interval = data["time_interval"]

    # Initialize sentiment analysis for each slug
    social_media_sentiment_data = {}
    social_media_sentiment_analysis = {}

    for slug in slugs:
        progress.update_status("sentiment_analyst_agent", slug, "social_sentiment_analysing")
    
        # 主要观察balance_total, 并且观察positive_total 和 negative_total的变化趋势并作为参考。
        # 先把这部分的功能都实现，然后作为数据，和说明一起喂给analyst。
        # sentiment_balance_total = get_sentiment_balance_total(
        #     slug = 'social_sentiment_weighted_total' + slug,
        #     end_date=end_date,
        #     start_date=start_date,    
        # )
        # print(sentiment_balance_total)
        # sentiment_negative_total = get_sentiment_negative_total(
        #     slug = 'social_sentiment_negative_total' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # )

        # sentiment_positive_total = get_sentiment_positive_total(
        #     slug = 'social_sentiment_positive_total' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # )


        # # 看看这部分是不是有在不断增加
        # # 都是从这一刻往前算的

        # progress.update_status("sentiment_analyst_agent", slug, "social_volume_analysing")
        # social_volume_total_change_7d = get_social_volume_total_change_7d(
        #     slug = 'social_volume_total_change_7d' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # )
        # # print(social_volume_total_change_7d)
        # social_volume_total_change_30d = get_social_volume_total_change_30d(
        #     slug = 'social_volume_total_change_30d' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # )
        # print(social_volume_total_change_30d)
        # social_volume_total_change_1d = get_social_volume_total_change_1d(
        #     slug = 'social_volume_total_change_1d' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # ) 
        
        # # 用多个时间窗口（例如 1 日、3 日、7 日）分别计算情绪 neg pos momentum
        # # 任意两个pos_mom > 0 就认为是正面情绪，否则负面情绪。
        # # Can be used as an auxiliary sentiment analysis tool， 
        # # calculate also the momentum of this value to show the trend
        # sentiment_weighted_data = get_sentiment_weighted_total(
        #     slug = 'social_sentiment_weighted_total' + slug,
        #     end_date=end_date,
        #     start_date=start_date,
        # )
        # # check 
        # # sentiment_weighted_signals = {
        # #     "signal": "positive",
        # #     "momentum": sentiment_weighted_data.momentum
        # # }
        # # sentiment_weighted_signals = {
        # #     "signal": "negative",
        # #     "momentum": sentiment_weighted_data.momentum
        # # }
        # # sentiment_weighted_signals = {
        # #     "signal": "neutral",
        # #     "momentum": sentiment_weighted_data.momentum
        # # }

        fear_and_greed_index = get_fear_and_greed_index(target_date = end_date)
        fgic=fear_and_greed_index.classification, 
        fgi=fear_and_greed_index.value
        fear_and_greed_signals = {
            "classification": fgic,
            "confidence": fgi ,
        }

        social_media_sentiment_data[slug] = {
            # "signal": overall_signal could be generated by the social media analyst.
            # "confidence": confidence could also be generated by the sentiment_analyst.
            # "strategy_signals": {
            #     "social_sentiment_analysis": {
            #         "signal": social_sentiment_signals["signal"],
            #         "confidence": round(social_sentiment_signals["confidence"] * 100),
            #         "trend": social_volume_signals["trend"]
            #     },
            #     "social_volume_analysis": {
            #         "signal": social_volume_signals["signal"],
            #         "confidence": round(social_volume_signals["confidence"] * 100),
            #         "trend": social_volume_signals["trend"]
            #     },
                # "social_weighted_signals": {
                #     "signal":                    
                # },
                "fear_and_greed_index": {
                    "classification": fear_and_greed_signals["classification"],
                    "index": fear_and_greed_signals["confidence"]
                }
            }
        

        progress.update_status("social_media_analyst", slug, "social_media_analysis")
        # define the social media analyst
        social_media_analyst_system_message = """
        You are a crypto social_media_analyst, 
        For your reference, the current date is {date}, we are looking at {cryptos}.

        Your main task:
        - Write a report
        - Give trading signal
        - GIve confidence level

        You analysis is based on the following data:
        -Fear and greed index:
            - Guided Line: The crypto market is highly emotional: prices rising trigger FOMO (“fear of missing out”), falling prices often cause panic-selling.
                - Extreme Fear (0–24) → investors are overly pessimistic → potential buying opportunity 
                - Extreme Greed (75–100) → investors are overly optimistic → risk of correction; consider selling or waiting 
                - Embrace the contrarian approach: “Be fearful when others are greedy, greedy when others are fearful.”
            - Your analysis is based on the following data (already extracted):
                - classification: {fear_and_greed_index_classification}
                - index: {fear_and_greed_index_value}


        Your output must consist of three parts:

        ---

        ### Part 1: **News Sentiment Report**
        - A structured report summarizing the news and trends.
        - Evaluation of news credibility and timeliness.
        - Assessment of the likely market impact.
        - Discussion of how crypto markets have typically responded to similar news in the past.

        ---

        ### Part 2: **Trading Signal**
        - Based on the report above, provide a clear trading signal.
        - The format must be: `Trading Signal: **Buy** / **Hold** / **Sell**`
        - Please return only the signal, no explanation.

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
        """.format(
            date=end_date, 
            cryptos=slug,
            fear_and_greed_index_classification=fgic, 
            fear_and_greed_index_value=fgi)

        social_media_analyst_agent = create_react_agent(
            llm,
            tools=[],
            state_modifier=social_media_analyst_system_message,
        )
        # Run the agent
        # message = news_analyst_agent.invoke([input_message])
        analyst_message = social_media_analyst_agent.invoke({"messages":messages})
        content = analyst_message["messages"][-1].content
        
        # Extract News Sentiment Report
        part1_match = re.search(
            r"### Part 1: \*\*News Sentiment Report\*\*\n\n(.*?)\n\n### Part 2:", 
            content, 
            re.DOTALL
            )
        social_media_report = part1_match.group(1).strip() if part1_match else None
        # print(news_report)

        # Extract Trading Signal
        part2_match = re.search(
            r"Part 2: \*\*Trading Signal\*\*.*?Trading Signal: \*\*(Buy|Hold|Sell)\*\*", 
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

        social_media_sentiment_analysis[slug] = {
            "signal": trading_signal,
            "confidence": confidence_level,
            "report": social_media_report,
        }    

        progress.update_status("social_media_analyst", slug, "Done")
    
    # Create the technical analyst message
    message = HumanMessage(
        content=json.dumps(social_media_sentiment_analysis),
        name="sentiment_analyst_agent",
    )

    return {"messages": [message], "data": state["data"]}

if __name__ == "__main__":

    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(AgentState)
    workflow.add_node("social_media_analyst", social_media_analyst)
    workflow.set_entry_point("social_media_analyst")
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