from openai import OpenAI
from langchain.tools import Tool
from typing import Optional


def analyze_social_trends_openai(
	topic: str, curr_date: str, model: str = 'gpt-4.1-mini'
) -> Optional[str]:
	"""
	Analyzes social media trends, sentiment, and discussions related to a specific topic or asset.
	"""
	client = OpenAI()

	response = client.responses.create(
		input=[
			{
				'role': 'system',
				'content': [
					{
						'type': 'input_text',
						'text': (
							f'Please act as a social media analyst.\n\n'
							f'Analyze the discussions, sentiment, and trend patterns related to "{topic}" '
							f'on platforms like Twitter (X), Reddit, Discord, and Telegram over the 7 days before {curr_date}.\n'
							f'Please provide:\n'
							f'1. Overall sentiment (positive/negative/neutral) with representative quotes\n'
							f'2. Most discussed subtopics or hashtags\n'
							f'3. Influential posts or viral opinions\n'
							f'4. Attention dynamics (e.g., spikes/dips in engagement)\n'
							f'5. Summary of public perception change (if any)\n'
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
				'search_context_size': 'medium',
			}
		],
		temperature=1,
		max_output_tokens=4096,
		top_p=1,
		store=True,
	)

	return response.output[1].content[0].text


langchain_tools = [
	Tool(
		name='SocialMediaTrendAnalyzer',
		func=lambda input_str: analyze_social_trends_openai(
			topic=input_str.split(',')[0].strip(),
			curr_date=input_str.split(',')[1].strip(),
		),
		description=(
			'Analyzes social media discussions, trends, and sentiment for a given topic.\n'
			"Input: 'topic, current_date' (e.g., 'Ethereum, 2025-07-28')."
		),
	),
]


if __name__ == '__main__':
	topic = 'Ethereum'
	current_date = '2025-07-28'

	social_trend_report = analyze_social_trends_openai(topic, current_date)

	print('Social Media Trend Report:\n', social_trend_report)
