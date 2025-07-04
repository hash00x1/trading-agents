from langgraph.prebuilt import create_react_agent
from base_workflow.tools.openai_news_crawler import langchain_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
import re
import json

def news_analyst(state: AgentState):
    ##### Financial News Sentiment Agent ###################################################################
    ### Generate a comprehensive analysis report of recent crypto news, focusing on sentiment and market impact.
    ### Give a trading signal for the news sentiment, which should suit the whole workflow.
    ### Give a confidence leve for the trading signal.
    #########################################################################################################
    messages = state.get("messages", [])
    data = state.get("data", {})
    end_date = data.get("end_date")
    slugs = data.get("slugs", [])
    llm = ChatOpenAI(model='gpt-4o-mini')
    # Initialize sentiment analysis
    news_sentiment_analysis = {}

    for slug in slugs:
        news_analyst_system_message = """
        You are a crypto news researcher, 
        You play as analyst assistant in a multi-agent system, focused on gathering and analysing news and trends.
        For your reference, the current date is {date}, we are looking at {cryptos}.

        Your main task:
        - Gather, analyze, and summarize recent news and market trends related to these cryptocurrencies.
        - Provide accurate, reliable, and actionable insights that support trading decisions and write into a report.

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
        """.format(date=end_date, cryptos=slug)

        news_analyst_agent = create_react_agent(
            llm,
            tools=langchain_tools,
            state_modifier=news_analyst_system_message,
        )
        # Run the agent
        # message = news_analyst_agent.invoke([input_message])
        analyst_message = news_analyst_agent.invoke({"messages":messages})
        content = analyst_message["messages"][-1].content
        
        # Extract News Sentiment Report
        part1_match = re.search(
            r"### Part 1: \*\*News Sentiment Report\*\*\n\n(.*?)\n\n### Part 2:", 
            content, 
            re.DOTALL
            )
        news_report = part1_match.group(1).strip() if part1_match else None
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

        news_sentiment_analysis[slug] = {
            "signal": trading_signal,
            "confidence": confidence_level,
            "report": news_report,
        }

    # Creat the news sentiment message
    message = HumanMessage(
        content=json.dumps(news_sentiment_analysis),
        name="sentiment_agent",
    )

    return {
        "messages": [message],
        "data": data,
    }


if __name__ == "__main__":

    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(AgentState)
    workflow.add_node("news_analyst", news_analyst)
    workflow.set_entry_point("news_analyst")
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
