from base_workflow.utils.debate_agent import DialogueSimulatorAgent, DialogueAgent
from base_workflow.agents import bearish_researcher, bullish_researcher
from typing import List
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)


class Trader(DialogueSimulatorAgent):
    """
    Evaluating recommendations and insights from analysts and researchers.
    Deciding on the timing and size of trades to maximize trading returns
    Placing buy or sell orders in the market.
    Adjusting portfolio allocations in response to market changes and new information.
    """
    def __init__(self, agents: List[DialogueAgent], rounds) -> None:
        super().__init__(agents=agents, rounds=rounds)


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


    def analysis(self) -> tuple[str, str]:
        log = super().run(initial_message="Let's discuss the potential of technology stocks in the current market.")
        # print it out:
        for speaker, text in log:
            print(f"({speaker}): {text}\n")
        return "trader", log



# Initialize the Trader agent
trader = Trader(agents = [bullish_researcher, bearish_researcher], rounds=6)       

# Example usage
if __name__ == "__main__":
  result = trader.analysis()
  print(result)

    