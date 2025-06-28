from langgraph.prebuilt import create_react_agent
from base_workflow.tools import scrape_news_pages


##### Financial News Sentiment Agent #####
### Maybe only for test use, later combine with the social_media_analyst.py ###

news_analyst_system_message = """
  Please scrape the following news sites for any headlines that mention "Bitcoin". 
  Return a list of these Bitcoin-related headlines, along with the URL of the site they came from.

  The sites are:
  - https://www.reuters.com/markets/cryptocurrency/
  - https://www.coindesk.com/
  - https://www.cnbc.com/cryptocurrency/

  If no Bitcoin headlines are found on a site, let me know that as well.
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

llm = ChatOpenAI(model='gpt-4o-mini')
news_analyst_tools = [scrape_news_pages]

news_analyst = create_react_agent(
    llm,
    tools=news_analyst_tools,
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
  