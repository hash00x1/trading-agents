from langgraph.prebuilt import create_react_agent
from base_workflow.tools.openai_news_crawler import langchain_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from langchain_core.messages import HumanMessage
from langgraph.types import Command
from typing import Literal
from base_workflow.graph.state import AgentState


from typing import Literal, Union
from chromadb.utils.rendezvous_hash import Members
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from sympy.strategies.rl import subs
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI

def news_analyst_node(state: AgentState):
    ##### Financial News Sentiment Agent ###################################################################
    ### Maybe only for test use, later combine with the social_media_analyst.py 
    ### Generate a comprehensive analysis of recent crypto news, focusing on sentiment and market impact.
    ### Give a final score for the news sentiment, which should suit the whole workflow.
    #########################################################################################################
    messages = state.get("messages", [])
    data = state.get("data", {})
    end_date = data.get("end_date")
    tickers = data.get("tickers")

    news_analyst_system_message = """
    You are a crypto news researcher, 
    You play as analyst assistant in a multi-agent system, focused on gathering and analysing recent news and trends over the past 2 weeks, 
    Your main task is to gather, analyze, and summarize recent news and market trends related to cryptocurrencies. 
    Focus on providing accurate, reliable, and actionable insights that can support traders and decision-makers.

    Your responsibilities:
    - Search for and analyze news from the past 14 days. If you cannot find sufficient relevant information, extend the search period to cover the past 30 days.
    - Prioritize trustworthy sources (e.g., CoinDesk, The Block, Bloomberg, Reuters).
    - Identify sentiment orientation of each news item (e.g., positive, negative, neutral) and assess its potential impact on the crypto market.
    - Highlight important factors such as: regulations, institutional adoption, market trends, security incidents, major partnerships, technological innovations, and macroeconomic events.
    - Provide fine-grained analysis, not just general statements like “trends are mixed.” Offer detailed insights that can help traders make informed decisions.

    Ensure your analysis:
    - Evaluates the credibility and timeliness of the news.
    - Assesses the scope of potential market impact.
    - Reflects how crypto markets typically respond to such news.

    Your output should be clear, structured, and focused on supporting intelligent trading decisions.
    """


    llm = ChatOpenAI(model='gpt-4o-mini')

    news_analyst_agent = create_react_agent(
        llm,
        tools=langchain_tools,
        state_modifier=news_analyst_system_message,
    )
    # Run the agent
    # message = news_analyst_agent.invoke([input_message])
    message = news_analyst_agent.invoke({"messages":messages})

    return {
        "messages": [message],
        "news_report": message["messages"][-1].content,
    }

# def news_analyst_node(state: AgentState) -> Command[Literal["technical_analyst"]]:
#     result = news_analyst.invoke(state)
#     return Command(
#         update={
#             'messages': [
#                 HumanMessage(content=result["messages"][-1].content, name='news')
#             ],
#             'news_report': result["messages"][-1].content
#         },
#         goto='technical_analyst'
#     )


if __name__ == "__main__":

    llm = ChatOpenAI(model="gpt-4o")

    workflow = StateGraph(AgentState)
    workflow.add_node("news_analyst", news_analyst_node)
    workflow.set_entry_point("news_analyst")
    research_graph = workflow.compile()

    # Initialize state with messages as a list
    initial_state = {
        "messages": [
            HumanMessage(content="Make trading decisions based on the provided data.")
            ]       
        ,
        "data": {
            "slugs": ["ohlcv/bitcoin"],
            "start_date": "2024-06-07",
            "end_date": "2024-08-08",
            "time_interval": "4h",
        },
        "metadata": {
            "request_id": "test-123",
            "timestamp": "2025-07-02T12:00:00Z"
        }
    }

    # Invoke the compiled graph
    final_state = research_graph.invoke(initial_state)

    # The result is a dict matching your AgentState schema
    print(final_state)
