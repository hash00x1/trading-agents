from typer.cli import state
from base_workflow.agents.debate_agent import DialogueAgentWithTools, DialogueSimulatorAgent, DialogueAgent
from base_workflow.agents import create_bearish_researcher, create_bullish_researcher
from typing import List
from langchain_openai import ChatOpenAI
from base_workflow.graph.state import AgentState
from langchain.schema import SystemMessage, HumanMessage
from typing import Optional
from copy import deepcopy
from typing_extensions import Literal
import json
from typing import Any

# analyst_team_conclusions = """
# ## Technical Analyst
# **Role**: Analyzes price trends and technical indicators.  
# **Summary**: Bitcoin shows signs of breakout above $60,000 with strong RSI.  
# **Signals**: RSI at 61, MACD positive crossover.  
# **Recommendation**: Buy on breakout.

# ## On-chain Analyst
# **Role**: Tracks wallet behavior and blockchain activity.  
# **Summary**: Exchange outflows and accumulation addresses increasing.  
# **Signals**: NVT ratio falling, inflows down 18%.  
# **Recommendation**: Hold or accumulate.

# ## Social Media Analyst
# **Role**: Assesses Twitter, Reddit, Google Trends sentiment.  
# **Summary**: Bullish sentiment surging, but overhype risk exists.  
# **Signals**: +36% Reddit mentions, bullish Twitter ratio 5:1.  
# **Recommendation**: Cautious Buy.

# ## News Analyst
# **Role**: Analyzes recent news headlines and narratives.  
# **Summary**: Spot Bitcoin ETF inflows remain strong; no major regulatory threats this week.  
# **Signals**: ETF net inflows +1.2B USD.  
# **Recommendation**: Hold with positive bias.

# """
class ResearchReport:
    signal: Literal["Buy", "Sell", "Hold"]
    report: str

class ResearchManager(DialogueSimulatorAgent):
    """
    Evaluating recommendations and insights from analysts and researchers.
    Deciding on the timing and size of trades to maximize trading returns
    Placing buy or sell orders in the market.
    Adjusting portfolio allocations in response to market changes and new information.
    """
    def __init__(self, rounds:int, state: Optional[AgentState] = None):
        self.research_analysis: dict[str, Any] = {} 
        self.model = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.data = state["data"]

        if state is None:
            state = AgentState(
                messages=[],
                data={},
                metadata={}
            )

        research_agents=[
           create_bullish_researcher(model=self.model, state=deepcopy(state)), 
           create_bearish_researcher(model=self.model, state=deepcopy(state))
           ]
        super().__init__(agents=research_agents, rounds=rounds)
        self.data = state["data"]


    def generate_report(self, conversation_log: str):
        analysis_prompt = f"""
        You are a financial analyst assistant. Your task is to read the conversation log between
        a Bullish Researcher and a Bearish Researcher. Based on this multi-round debate, please generate
        a structured research report to assist a trader in making an informed trading decision,
        in the last chapter on the report, you must give a actionable signal.

        Conversation Log:
        {conversation_log}

        The report should follow this structure:
        
            # Executive Summary
            Briefly summarize the overall market outlook, key talking points, and your final recommendation (Buy / Sell / Hold). 
            This should be concise (3–5 lines), easy to read, and understandable to a portfolio manager.

            # Market Signals
            ## Bullish Signals
            List arguments or indicators supporting a positive outlook. Reference specific insights or arguments from the Bullish Researcher.

            ## Bearish Signals
            List arguments or indicators supporting a negative outlook. Reference specific insights or arguments from the Bearish Researcher.

            ## Quantitative Analysis
            Summarize any numerical indicators discussed or implied (e.g., RSI, MACD, volume trends, volatility).

            # Sentiment & Fundamental Factors
            Summarize qualitative insights (e.g., macro trends, news impact, regulatory changes, social sentiment, research articles) 
            derived from the conversation or tools used.

            # Data Summary
            List metadata related to the analysis:
            - Assets discussed
            - Time interval
            - Date range
            - Tools or sources used by agents (e.g., arxiv, wikipedia)

            # Final Recommendation
            - Based on the report above, provide a clear trading signal.
            - The format must be: `Trading Signal: **Buy** / **Hold** / **Sell**`
            - Please return only the signal, no explanation.

            Please return only the research report, formatted using Markdown-style headers.
        """

        # Call the LLM to get the analysis
        report = self.model.invoke([
                SystemMessage(content="You are a financial report assistant. Your task is..."),
                HumanMessage(content=analysis_prompt)
            ])
        signal_prompt = f"""
            Based on the following report, output the final trading signal only.

            {report}

            Please return only one line in this format:
            Trading Signal: **Buy** / **Sell** / **Hold**
            """
        signal = self.model.invoke([HumanMessage(content=signal_prompt)])
        self.research_analysis = {
            "signal": signal,
            "report": report,
        }
        
        message = HumanMessage(
            content = json.dumps(self.research_analysis),
            name = "research_manager"
        )      
        
        return {
            "messages":[message],
            "data": self.data          
        }

    def analysis(self, knowledge) -> str:
        # use the real data from the conversation log to feed the system.
        log = super().run(knowledge=knowledge)
        for speaker, text in log:
            print(f"({speaker}): {text}\n")

        str_log = str(log)
        return str_log
    
    def __call__(self, knowledge: str):
        log = self.analysis(knowledge)
        return self.generate_report(conversation_log=log)


research_manager = ResearchManager(rounds= 6)

# Test the Trader agent
if __name__ == "__main__":
    test_state = AgentState(
        messages=[],
        data={
            "tickers": ["ohlcv/bitcoin" ],
            "start_date": "2024-06-07",
            "end_date": "2024-08-08",
            "time_interval": "4h",
        },
        metadata={"show_reasoning": False},
    )
    initial_knowledge = "Please discuss Bitcoin's investment potential over the next 6 months."
    result = research_manager.analysis(knowledge=initial_knowledge)
    reply = research_manager.generate_report(conversation_log=result)
    print(result)

    