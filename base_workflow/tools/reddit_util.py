import os
import json
import re
from datetime import datetime
from typing import Annotated, List


data_path = 'base_workflow/data/reddit_data'
category = 'crypto_news'


def fetch_top_from_category(
	category: Annotated[str, "Category to fetch top posts from. E.g., 'crypto_news'"],
	date: Annotated[str, 'Date to fetch top posts from, in yyyy-mm-dd format'],
	max_limit: Annotated[int, 'Maximum number of posts to fetch.'],
	keywords: Annotated[
		List[str], 'List of keywords to match in title/content.'
	] = None,
	data_path: Annotated[
		str, 'Path to data directory containing category subfolders.'
	] = 'base_workflow/data/reddit_data',
) -> List[dict]:
	"""
	Fetch Reddit posts from a given category and date, filtering by keywords (e.g., slug or token).
	Each subreddit is assumed to have its own .jsonl file in the category directory.

	Returns:
	    A list of filtered post dictionaries with keys: title, content, url, upvotes, posted_date
	"""
	base_path = data_path
	category_path = os.path.join(base_path, category)

	if not os.path.exists(category_path):
		raise FileNotFoundError(f'Category path not found: {category_path}')

	subreddit_files = [f for f in os.listdir(category_path) if f.endswith('.jsonl')]

	if not subreddit_files:
		raise ValueError('No valid subreddit .jsonl files found in the category path.')

	if max_limit < len(subreddit_files):
		raise ValueError(
			'Reddit fetching error: max_limit is smaller than the number of subreddit files. '
			'Increase max_limit or reduce the number of subreddits.'
		)

	limit_per_subreddit = max_limit // len(subreddit_files)
	all_posts = []

	for filename in subreddit_files:
		full_path = os.path.join(category_path, filename)
		posts_in_file = []

		with open(full_path, 'r', encoding='utf-8') as f:
			for line in f:
				if not line.strip():
					continue

				post_data = json.loads(line)
				post_date = datetime.utcfromtimestamp(
					post_data['created_utc']
				).strftime('%Y-%m-%d')
				if post_date != date:
					continue

				# keyword filtering (slug/token)
				if keywords:
					content_to_search = (
						post_data.get('title', '') + ' ' + post_data.get('selftext', '')
					)
					if not any(
						re.search(k, content_to_search, re.IGNORECASE) for k in keywords
					):
						continue

				posts_in_file.append(
					{
						'title': post_data.get('title', ''),
						'content': post_data.get('selftext', ''),
						'url': post_data.get('url', ''),
						'upvotes': post_data.get('ups', 0),
						'posted_date': post_date,
					}
				)

		posts_in_file.sort(key=lambda x: x['upvotes'], reverse=True)
		all_posts.extend(posts_in_file[:limit_per_subreddit])

	return all_posts


if __name__ == '__main__':
	data_path = 'base_workflow/data/reddit_data'
	category = 'crypto_news'
	date = '2025-07-25'  # 修改为你实际有数据的日期
	max_limit = 10
	keywords = ['bitcoin', 'ethereum', 'crypto', 'blockchain']  # 可选关键词过滤

	try:
		top_posts = fetch_top_from_category(
			category=category,
			date=date,
			max_limit=max_limit,
			keywords=keywords,
			data_path=data_path,
		)

		print(f'\nFetched {len(top_posts)} posts for date {date}:\n')
		for i, post in enumerate(top_posts, start=1):
			print(f'--- Post #{i} ---')
			print(f'Title: {post["title"]}')
			print(f'Upvotes: {post["upvotes"]}')
			print(f'URL: {post["url"]}')
			print(f'Date: {post["posted_date"]}')
			print(f'Content: {post["content"][:150]}...')  # 限制预览长度
			print()

	except Exception as e:
		print(f'Error: {e}')
