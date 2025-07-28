from openai import OpenAI
from langchain.tools import Tool

from typing import List
import requests
from bs4 import BeautifulSoup


def scrape_news_pages(urls: List[str], coin_name: str) -> str:
	"""
	Scrape and retrieve crypto headlines from a list of news page URLs.

	Args:
	    urls (List[str]): A list of news article URLs to scrape.
	    coin_name (str): The name of the cryptocurrency to search for (e.g., 'bitcoin', 'ethereum').

	Returns:
	    str: A formatted string containing the extracted coin-related headlines from each URL.
	        Headlines are wrapped in a <Document> tag that includes the source URL.
	        If an error occurs for a URL, the error message is returned within the <Document> tag.
	"""
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
				if text and coin_name.lower() in text.lower():
					headlines.append(text)

			# Create document-style output
			result = f'<Document url="{url}">\n'
			for idx, hl in enumerate(headlines, 1):
				result += f'Headline {idx}: {hl}\n'
			result += '</Document>\n'

			all_results.append(result)

		except Exception as e:
			all_results.append(
				f'<Document url="{url}">\nError: {str(e)}\n</Document>\n'
			)

	return '\n'.join(all_results)


def get_crypto_social_news_openai(crypto_name: str, curr_date: str):
	"""
	Fetches crypto social and discussion news from reliable sources for a specific cryptocurrency.
	"""
	client = OpenAI()

	response = client.responses.create(
		model='gpt-4.1-mini',
		input=[
			{
				'role': 'system',
				'content': [
					{
						'type': 'input_text',
						'text': (
							f'Can you search search reliable news sources (such as CoinDesk, The Block, Bloomberg, Reuters, etc.) '
							f'for news and discussions about {crypto_name} from 7 days before {curr_date}? '
						),
					}
				],
			}
		],
		text={'format': {'type': 'text'}},
		reasoning={},
		tools=[
			{
				'type': 'web_search_preview',
				'user_location': {'type': 'approximate'},
				'search_context_size': 'low',
			}
		],
		temperature=1,
		max_output_tokens=4096,
		top_p=1,
		store=True,
	)

	return response.output[1].content[0].text


def get_crypto_global_news_openai(curr_date: str):
	"""
	Fetches global or macroeconomic crypto-related news from reliable sources.
	"""
	client = OpenAI()

	response = client.responses.create(
		model='gpt-4.1-mini',
		input=[
			{
				'role': 'system',
				'content': [
					{
						'type': 'input_text',
						'text': (
							f'Can you search for global or macroeconomic news specifically related to cryptocurrencies '
							f'(like regulations, market trends, institutional adoption, etc.) from 7 days before {curr_date}? '
							f'Only include news published during that period.'
						),
					}
				],
			}
		],
		text={'format': {'type': 'text'}},
		reasoning={},
		tools=[
			{
				'type': 'web_search_preview',
				'user_location': {'type': 'approximate'},
				'search_context_size': 'low',
			}
		],
		temperature=1,
		max_output_tokens=4096,
		top_p=1,
		store=True,
	)

	return response.output[1].content[0].text


langchain_tools = [
	# Tool(
	#     name="CryptoNewsScraperTool",
	#     func=lambda input_str: scrape_news_pages(
	#         urls=[u.strip() for u in input_str.split("|")[0].split(",")],
	#         coin_name=input_str.split("|")[1].strip()
	#     ),
	#     description=(
	#         "Scrapes crypto-related headlines from a list of URLs. "
	#         "Input format: 'url1,url2,url3 | coin_name' (e.g., 'https://site1.com, https://site2.com | Bitcoin')."
	#     ),
	# ),
	Tool(
		name='CryptoSocialNewsTool',
		func=lambda input_str: get_crypto_social_news_openai(
			crypto_name=input_str.split(',')[0].strip(),
			curr_date=input_str.split(',')[1].strip(),
		),
		description="Fetches crypto social and discussion news. Input: 'crypto_name, current_date' (e.g., 'Bitcoin, 2025-06-11').",
	),
	Tool(
		name='CryptoGlobalNewsTool',
		func=lambda input_str: get_crypto_global_news_openai(
			curr_date=input_str.strip()
		),
		description="Fetches global or macroeconomic crypto-related news. Input: 'current_date' (e.g., '2025-06-11').",
	),
]

if __name__ == '__main__':
	# Example usage
	crypto_name = 'Bitcoin'
	current_date = '2025-06-11'

	social_news = get_crypto_social_news_openai(crypto_name, current_date)
	macro_news = get_crypto_global_news_openai(current_date)

	print('Social Media News:\n', social_news)
	print('\nGlobal Crypto News:\n', macro_news)
