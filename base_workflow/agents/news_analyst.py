from langgraph.prebuilt import create_react_agent
from base_workflow.tools.openai_news_crawler import langchain_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

##### Financial News Sentiment Agent ###################################################################
### Maybe only for test use, later combine with the social_media_analyst.py 
### Generate a comprehensive analysis of recent crypto news, focusing on sentiment and market impact.
### Give a final score for the news sentiment, which should suit the whole workflow.
#########################################################################################################
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

news_analyst = create_react_agent(
    llm,
    tools=langchain_tools,
    state_modifier=news_analyst_system_message,
)

if __name__ == "__main__":
    # Define a simple input for the agent
    inputs = {"messages": [("user", "Please scrape the news sites for Bitcoin headlines.")]}
    for s in news_analyst.stream(inputs, stream_mode="values"):
         message = s["messages"][-1]
         if isinstance(message, tuple):
             print(message)
         else:
             message.pretty_print()
  