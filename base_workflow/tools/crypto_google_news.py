# Notes: this script does not work properly yet, it doesn't scrape the news articles.
# 1. Install and Import Baseline Dependencies
from bs4 import BeautifulSoup
import requests
import re
# google API 
# 3. Setup Pipeline
monitored_tickers = ['ETH']

# 4.1. Search for Stock News using Google and Yahoo Finance
print('Searching for stock news for', monitored_tickers)
def search_for_stock_news_links(ticker):
    search_url = 'https://www.google.com/search?q=yahoo+finance+{}&tbm=nws'.format(ticker)
    r = requests.get(search_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atags = soup.find_all('a')
    hrefs = [link['href'] for link in atags]
    return hrefs

raw_urls = {ticker:search_for_stock_news_links(ticker) for ticker in monitored_tickers}

# 4.2. Strip out unwanted URLs
print('Cleaning URLs.')
exclude_list = ['maps', 'policies', 'preferences', 'accounts', 'support']
def strip_unwanted_urls(urls, exclude_list):
    val = []
    for url in urls:
        if 'https://' in url and not any(exc in url for exc in exclude_list):
            res = re.findall(r'(https?://\S+)', url)[0].split('&')[0]
            val.append(res)
    return list(set(val))

cleaned_urls = {ticker:strip_unwanted_urls(raw_urls[ticker] , exclude_list) for ticker in monitored_tickers} 

# 4.3. Search and Scrape Cleaned URLs
print('Scraping news links.')
def scrape_and_process(URLs):
    ARTICLES = []
    for url in URLs:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        results = soup.find_all('p')
        text = [res.text for res in results]
        words = ' '.join(text).split(' ')[:350]
        ARTICLE = ' '.join(words)
        ARTICLES.append(ARTICLE)
    return ARTICLES
articles = {ticker:scrape_and_process(cleaned_urls[ticker]) for ticker in monitored_tickers} 
print('Scraped articles:', articles)