from typer.cli import state
from base_workflow.agents.debate_agent import DialogueAgentWithTools, DialogueSimulatorAgent, DialogueAgent
from base_workflow.agents import bearish_researcher, bullish_researcher
from typing import List
from langchain_openai import ChatOpenAI
from base_workflow.graph.state import AgentState


llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)


class Researchmanager(DialogueSimulatorAgent):
    """
    Evaluating recommendations and insights from analysts and researchers.
    Deciding on the timing and size of trades to maximize trading returns
    Placing buy or sell orders in the market.
    Adjusting portfolio allocations in response to market changes and new information.
    """
    def __init__(self, trader_agents: List[DialogueAgentWithTools], rounds) -> None:
        super().__init__(agents=trader_agents, rounds=rounds)


    def analyze_conversation(self, conversation_log: List[tuple[str, str]]) -> str:      # Use the LLM to summarize and analyze the conversation log
      analysis_prompt = f"""
      Please analyze the following conversation between the Analyst and Researcher. 
      Provide insights based on both quantitative and qualitative factors to help the 
      Trader make an informed trading decision.

      Conversation Log:
      {conversation_log}

      Analysis:
      - Summarize key insights
      - Highlight any important trends, quantitative data, or qualitative insights
      - Provide a recommendation for the next trading action (buy, sell, hold, etc.)
      """

      # Call the LLM to get the analysis
      analysis = self.model.predict(analysis_prompt)
      return analysis

    def analysis(self, knowledge) -> str:
        # use the real data from the conversation log to feed the system.
        log = super().run(knowledge=knowledge)
        for speaker, text in log:
            print(f"({speaker}): {text}\n")

        str_log = str(log)
        return str_log

    # def analysis(self, knowledge) -> tuple[str, str]:
    #     # use the real data from the conversation log to feed the system.
    #     log = super().run(knowledge=knowledge)
    #     for speaker, text in log:
    #         print(f"({speaker}): {text}\n")

    #     str_log = str(log)
    #     return "trader", log


# Initialize the Trader agent
# trader = Trader(trader_agents=[bullish_researcher, bearish_researcher], rounds=6)       

# Test the Trader agent
# if __name__ == "__main__":
#   result = trader.analysis()
#   print(result)

    