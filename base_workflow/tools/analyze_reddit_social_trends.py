from datetime import datetime
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
from typing import Annotated
from reddit_util import fetch_top_from_category

data_path = 'base_workflow/data/reddit_data'
category = 'crypto_project_news'


def get_reddit_slug_token_news(
	slug: Annotated[str, "Project slug, e.g., 'bitcoin', 'uniswap', etc."],
	token: Annotated[str, "Token symbol, e.g., 'BTC', 'UNI', etc."],
	start_date: Annotated[str, 'Start date in yyyy-mm-dd format'],
	look_back_days: Annotated[int, 'How many days to look back'],
	max_limit_per_day: Annotated[int, 'Maximum number of posts to fetch per day'],
) -> str:
	"""
	Retrieve Reddit posts related to a given slug/token in the given date range.

	Args:
	    slug: Slug of the crypto project (e.g., 'ethereum')
	    token: Token symbol (e.g., 'ETH')
	    start_date: Analysis end date in yyyy-mm-dd format
	    look_back_days: How many days to look back before start_date
	    max_limit_per_day: Max Reddit posts to fetch per day

	Returns:
	    str: Formatted Markdown-style string of Reddit posts and meta info
	"""

	start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
	before_dt = start_date_dt - relativedelta(days=look_back_days)
	before_str = before_dt.strftime('%Y-%m-%d')

	posts = []
	curr_date = before_dt

	total_iterations = (start_date_dt - before_dt).days + 1
	pbar = tqdm(
		desc=f'Fetching Reddit News for {slug.upper()} / {token.upper()}',
		total=total_iterations,
	)

	while curr_date <= start_date_dt:
		curr_date_str = curr_date.strftime('%Y-%m-%d')

		fetch_result = fetch_top_from_category(
			category='crypto_project_news',
			date=curr_date_str,
			max_limit=max_limit_per_day,
			keywords=[slug, token],
			data_path='/Users/tai/my_project/data/reddit_data',
		)

		posts.extend(fetch_result)
		curr_date += relativedelta(days=1)
		pbar.update(1)

	pbar.close()

	if not posts:
		return f'No Reddit posts found for {slug} / {token} between {before_str} and {start_date}.'

	news_str = f'## Reddit News for `{slug}` / `{token}`, from {before_str} to {start_date}:\n\n'
	for post in posts:
		if post.get('content', '') == '':
			news_str += f'### {post["title"]}\n\n'
		else:
			news_str += f'### {post["title"]}\n\n{post["content"]}\n\n'

	return news_str


if __name__ == '__main__':
	result = get_reddit_slug_token_news(
		slug='solana',
		token='SOL',
		start_date='2025-07-28',
		look_back_days=7,
		max_limit_per_day=25,
	)
	print(result)
