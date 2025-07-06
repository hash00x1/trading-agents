from typing import List
import requests
from bs4 import BeautifulSoup
from typing import Annotated, List
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

@tool
def scrape_news_pages(urls: List[str]) -> str:
    """Scrape the provided news web pages for headlines and summaries."""
    all_results = []

    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Example: extract <h1>, <h2>, or <h3> tags as headlines
            headlines = []
            for tag in soup.find_all(['h1', 'h2', 'h3']):
                text = tag.get_text(strip=True)
                if text and 'bitcoin' in text.lower():
                    headlines.append(text)
            
            # Create document-style output
            result = f'<Document url="{url}">\n'
            for idx, hl in enumerate(headlines, 1):
                result += f'Headline {idx}: {hl}\n'
            result += '</Document>\n'
            
            all_results.append(result)

        except Exception as e:
            all_results.append(f'<Document url="{url}">\nError: {str(e)}\n</Document>\n')
    
    return "\n".join(all_results)
