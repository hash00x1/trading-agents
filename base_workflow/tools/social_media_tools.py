from openai import OpenAI
from langchain.tools import tool
from typing import Optional
from base_workflow.data.models import FearGreedIndex
import requests
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
import pandas as pd


@tool
def analyze_social_trends_openai(
	topic: str, curr_date: str, model: str = 'gpt-4.1-mini'
) -> Optional[str]:
	"""
	Analyzes social media trends, sentiment, and discussions related to a specific topic or asset.
	"""
	client = OpenAI()
	response = client.responses.create(
		model=model,
		input=[
			{
				'role': 'system',
				'content': [
					{
						'type': 'input_text',
						'text': (
							f'Please act as a cryptos social media analyst.\n\n'
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


@tool
def get_fear_and_greed_index(target_date: Optional[str] = None) -> FearGreedIndex:
	"""
	Fetch the Fear and Greed Index from the Alternative.me API.

	This tool measures the current sentiment of the crypto market to help guide investment decisions.
	The index ranges from 0 to 100 and reflects how fearful or greedy investors are on a given day.

	Interpretation of index values:
		- 0–24 (Extreme Fear): Investors are overly pessimistic — potential buying opportunity.
		- 25–49 (Fear): Market sentiment is cautious.
		- 50–54 (Neutral): Balanced market sentiment.
		- 55–74 (Greed): Optimistic sentiment — monitor for overvaluation.
		- 75–100 (Extreme Greed): Investors are overly optimistic — potential risk of correction.

	Args:
		target_date (Optional[str]): Date in YYYY-MM-DD format. Defaults to the latest available data if not specified.

	Returns:
		FearGreedIndex: A structured object containing the index value and its corresponding classification.
	"""
	try:
		# If target_date is provided, format it to the required date format
		if target_date:
			response = requests.get(
				'https://api.alternative.me/fng/?limit=0&date_format=cn'
			)
			fng = response.json()
			df = pd.DataFrame(fng['data'])
			index_data = df[df['timestamp'] == target_date]
			index_value = str(index_data['value'].iloc[0])
			classification = str(index_data['value_classification'].iloc[0])
			updated_at = target_date
		else:
			response = requests.get(
				'https://api.alternative.me/fng/?limit=1&date_format=cn'
			)
			data = response.json()
			index_data = data['data'][0]
			index_value = str(index_data['value'])
			classification = index_data['value_classification']
			updated_at = index_data['timestamp']
			# dt = datetime.strptime(timestamp, "%d-%m-%Y").replace(tzinfo=timezone.utc)
			# updated_at = dt.strftime("%Y-%m-%d")

		result = FearGreedIndex(
			value=index_value, classification=classification, updated_at=updated_at
		)
		return result

	except requests.RequestException as e:
		print(f'Error fetching Fear and Greed Index: {e}')
		return FearGreedIndex(
			value='0', classification='neutral', updated_at='Unknown'
		)  # set to neutral if error occurs


if __name__ == '__main__':
	llm = ChatOpenAI(model='gpt-4', temperature=0)

	agent = initialize_agent(
		tools=[get_fear_and_greed_index, analyze_social_trends_openai],
		llm=llm,
		agent=AgentType.OPENAI_FUNCTIONS,
		verbose=False,
	)

	result = agent.invoke(
		{'input': 'can you analyze the social media trends for Bitcoin on 2025-07-20?'}
	)
