from langchain_core.messages import HumanMessage
from base_workflow.graph.state import AgentState
from base_workflow.utils.progress import progress
from langchain_openai import ChatOpenAI
import json
import re
from pydantic import BaseModel
from typing_extensions import Literal
from langgraph.graph import StateGraph
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy.stats import linregress
from langchain.agents import initialize_agent, AgentType
from base_workflow.tools import (
	get_fear_and_greed_index,
	analyze_social_trends_openai,
)


class SocialMediaAnalystSignal(BaseModel):
	"""
	Container for the social media analyst output signal.
	"""

	signal: Literal['bullish', 'bearish', 'neutral']
	confidence: float
	report: str


##### Social Media Sentiment Agent #####
# the sentiment API from santiment
# sentiment_weighted_total: An improved version of the Sentiment Balance that adjusts the values by considering the number of mentions,
#                            standardizing data to make diverse asset sentiments comparable.
# sentiment_negative_total, sentiment_positive_total: Shows how many mentions of a term/asset are expressed in a positive/negative manner.
# sentiment_balance_total:  The difference between Positive Sentiment and Negative Sentiment
# social_volume_total,
# social_volume_total_change_30d,
# social_volume_total_change_7d,
# social_volume_total_change_1d,
# fear and greed index
##########################################
# Social Volume analysis
# mainly use momentum indicates the changes in social media activity around a cryptocurrency
# sentiment_weighted_total: 看看怎么用

# sentiment_positive_total: 计算momentum
# sentiment_negative_total: 计算momentum,两个看看哪个的增长速度快
# sentiment_balance_total: 看看是正面高还是负面高
# social_volume: 看看是否有人持续关注，并且关注的人数在不断增长

# fear_and_greed_index:

##############################################################################################################


def social_media_analyst(state: AgentState):
	"""Analyzes sentiment signals and generates trading signals for multiple slugs."""
	"""The initiative lies with the sentiment analyst, 
    who decides to generate reports and gives the final trading signals."""
	social_media_sentiment_analysis = {}
	data = state.get('data', {})
	end_date_str = data.get('end_date')
	end_date = datetime.strptime(str(end_date_str), '%Y-%m-%d')
	start_date = end_date - timedelta(weeks=2)
	start_date = start_date.strftime('%Y-%m-%d')

	slug = str(data.get('slug'))
	llm = ChatOpenAI(model='gpt-4o-mini')
	sentiment_tools = [
		get_fear_and_greed_index,
		analyze_social_trends_openai,
	]

	## Only use when the subscribtion include real-time data
	# _, sentiment_balance_total = get_sentiment_balance_total(
	# 	slug,
	# 	end_date=str(end_date),
	# 	start_date=start_date,
	# )
	# sentiment_balance_signal = analyse_sentiment_balance(sentiment_balance_total)

	# # define > 0. In the past 7 days, more than half > 0 can be considered as positive
	# _, sentiment_negative_total = get_sentiment_negative_total(
	# 	slug,
	# 	end_date=str(end_date),
	# 	start_date=start_date,
	# )

	# _, sentiment_positive_total = get_sentiment_positive_total(
	# 	slug,
	# 	end_date=str(end_date),
	# 	start_date=start_date,
	# )

	# sentiment_negative_growth_signal = sentiment_linear_regression(
	# 	sentiment_negative_total
	# )

	# sentiment_positive_growth_total = sentiment_linear_regression(
	# 	sentiment_positive_total
	# )

	# progress.update_status(
	# 	'sentiment_analyst_agent', slug, 'social_volume_analysing'
	# )

	progress.update_status(
		'social_media_analyst', slug, 'Summarizing and generating report'
	)
	# define the social media analyst
	social_media_analyst_system_message = """
	You are a crypto social_media_analyst, 
	For your reference, the current date is {date}, we are looking at {crypto}.

	Your main task:
	- Write a report
	- Give trading signal
	- Give confidence level

	You have access to the following tools:
	- `get_fear_and_greed_index(target_date: str)`: Retrieves the crypto fear and greed index from Alternative.me for the given date.
	- `analyze_social_trends_openai(topic: str, curr_date: str)`: Returns a social sentiment and trend analysis based on crypto discussions across major platforms.

	You must use these tools to enrich your sentiment analysis and trading decision.

	Your output must consist of three parts:

	---

	### Part 1: **Social Media Sentiment Report**
	- A structured report summarizing the news and trends.
	- Evaluation of news credibility and timeliness.
	- Assessment of the likely market impact.
	- Discussion of how crypto markets have typically responded to similar news in the past.

	---

	### Part 2: **Trading Signal**
	- Based on the report above, provide a clear trading signal.
	- The format must be: `Trading Signal: **Buy** / **Hold** / **Sell**`
	- Please return only the signal, no explanation.

	---

	### Part 3: **Confidence Level** 
	- Provide a confidence level for your signal as a float number.
	- The format must be: `Confidence Level: <float number>`
	- This number represents how confident you are in your signal, where:
		- 1 indicates extremely positive sentiment
		- 0.5 to 0.9 indicates positive sentiment
		- 0.1 to 0.4 indicates slightly positive sentiment 
		- 0 indicates neutral sentiment 
		- -0.1 to -0.4 indicates slightly negative sentiment
		- -0.5 to -0.9 indicates negative sentiment
		- -1 indicates extremely negative sentiment
	- Please return only the float number, no explanation.

	---
	""".format(
		date=end_date,
		crypto=slug,
	)
	social_media_agent = initialize_agent(
		tools=sentiment_tools,
		llm=llm,
		agent=AgentType.OPENAI_FUNCTIONS,
		verbose=True,
	)
	# Just invoke the message is enough here.
	content = social_media_agent.run(social_media_analyst_system_message)

	# Extract Social Media Sentiment Report
	part1_match = re.search(
		r'### Part 1:\s+\*\*Social Media\s+Sentiment\s+Report\*\*\s*\n+(.*?)(?=\n+---\n+\n+### Part 2:)',
		content,
		re.DOTALL,
	)
	social_media_report = part1_match.group(1).strip() if part1_match else None
	# print(news_report)

	# Extract Trading Signal
	part2_match = re.search(
		r'### Part 2: \*\*Trading Signal\*\*.*?Trading Signal: \*\*(Buy|Hold|Sell)\*\*',
		content,
		re.DOTALL,
	)
	trading_signal = part2_match.group(1) if part2_match else None
	# print(trading_signal)

	# Extract Confidence Level
	part3_match = re.search(
		r'### Part 3: \*\*Confidence Level\*\*.*?Confidence Level: ([\-\d\.]+)',
		content,
		re.DOTALL,
	)
	confidence_level = float(part3_match.group(1)) if part3_match else None
	# print(confidence_level)

	social_media_sentiment_analysis = {
		'signal': trading_signal,
		'confidence': confidence_level,
		'report': social_media_report,
	}

	progress.update_status('social_media_analyst', slug, 'Done')

	# Create the technical analyst message
	message = HumanMessage(
		content=json.dumps(social_media_sentiment_analysis),
		name='sentiment_analyst_agent',
	)

	return {'messages': [message], 'data': state['data']}


def analyse_sentiment_balance(df: pd.DataFrame):
	"""
	Analyze sentiment balance data using EMA and MACD to assess overall sentiment trend and momentum.

	The function applies:
	- A short-term EMA-based check to determine if the majority of sentiment values over the last 2 days are positive or negative.
	- A MACD analysis to detect bullish or bearish momentum shifts based on recent sentiment data.

	Returns:
	    dict: {
	        'sentiment': str,
	            Either 'positive' (majority of recent sentiment bars are positive)
	            or 'negative' (majority are negative)
	            or 'neutral' (no clear majority)
	        'macd_signal': str,
	            Either 'bullish' (MACD line crossed above signal line, momentum strengthening),
	            'bearish' (MACD line crossed below signal line, momentum weakening),
	            or 'neutral' (no significant crossover)
	    }
	"""

	bars_2d = 3 * 6
	df['ema_3'] = df['value'].ewm(span=bars_2d).mean()
	recent = df['ema_3'].tail(bars_2d)

	positive_count = (recent > 0).sum()
	if positive_count > bars_2d / 2:
		sentiment = 'positive'
	elif positive_count < bars_2d / 2:
		sentiment = 'negative'
	else:
		sentiment = 'neutral'

	ema_12 = df['value'].ewm(span=12, adjust=False).mean()
	ema_26 = df['value'].ewm(span=26, adjust=False).mean()
	macd = ema_12 - ema_26
	signal = macd.ewm(span=9, adjust=False).mean()
	hist = macd - signal

	macd_df = pd.DataFrame({'macd': macd, 'signal': signal, 'hist': hist})
	last = macd_df.iloc[-2:]
	macd_prev, sig_prev = last['macd'].iloc[0], last['signal'].iloc[0]
	macd_now, sig_now = last['macd'].iloc[1], last['signal'].iloc[1]

	if macd_prev < sig_prev and macd_now > sig_now:
		macd_signal = 'bullish'
	elif macd_prev > sig_prev and macd_now < sig_now:
		macd_signal = 'bearish'
	else:
		macd_signal = 'neutral'

	return {'sentiment': sentiment, 'macd_signal': macd_signal}


def sentiment_linear_regression(df):
	"""
	Performs linear regression on sentiment scores over time to identify sentiment trend.

	Returns:
	    dict: {
	        'signal': str,
	            Either 'positive' (upward trend) or 'negative' (downward trend)
	        'metrics': dict,
	            Contains:
	                - 'slope' (float): The regression slope, indicating average sentiment change per time unit.
	                - 'p_value' (float): Statistical significance of the slope.
	    }
	"""
	x = np.arange(len(df))
	y = df['value']
	slope, _, _, p_value, _ = linregress(x, y)  # "_" are interception, r_value, std_err

	slope = float(slope)
	p_value = float(p_value)

	if slope > 0:
		sentiment_signal = 'positive'
	elif slope < 0:
		sentiment_signal = 'negative'
	else:
		sentiment_signal = 'neutral'

	return {
		'sentiment_signal': sentiment_signal,
		'metrics': {
			'slope': slope,
			# "intercept": intercept,
			# "r_squared": r_squared,
			'p_value': p_value,
		},
	}


if __name__ == '__main__':
	llm = ChatOpenAI(model='gpt-4o')

	workflow = StateGraph(AgentState)
	workflow.add_node('social_media_analyst', social_media_analyst)
	workflow.set_entry_point('social_media_analyst')
	research_graph = workflow.compile()

	# Initialize state with messages as a list
	initial_state = {
		'messages': [
			HumanMessage(content='Make trading decisions based on the provided data.')
		],
		'data': {
			'slugs': ['bitcoin'],
			'start_date': '2024-06-07',
			'end_date': '2024-08-08',
			'time_interval': '4h',
		},
		'metadata': {'request_id': 'test-123', 'timestamp': '2025-07-29T12:00:00Z'},
	}

	final_state = research_graph.invoke(initial_state)

	print(final_state)
