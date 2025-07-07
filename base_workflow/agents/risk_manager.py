from base_workflow.agents.debate_agent import DialogueAgentWithTools, DialogueSimulatorAgent, DialogueAgent
from typing import List
from langchain_openai import ChatOpenAI
from base_workflow.agents import aggressive_risk_manager, conservative_risk_manager, neutral_risk_manager
from base_workflow.graph.state import AgentState



llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)


class RiskManager(DialogueSimulatorAgent):
    """
    Evaluating recommendations and insights from analysts and researchers.
    Deciding on the timing and size of trades to maximize trading returns
    Placing buy or sell orders in the market.
    Adjusting portfolio allocations in response to market changes and new information.
    """
    def __init__(self, portfolio_agents: List[DialogueAgentWithTools], rounds) -> None:
        super().__init__(agents=portfolio_agents, rounds=rounds)


    def analyze_conversation(self, conversation_log: List[tuple[str, str]]) -> str:      # Use the LLM to summarize and analyze the conversation log
      analysis_prompt = f"""
      Please analyze the following conversation between the Analyst and Researcher. 
      Provide insights based on both quantitative and qualitative factors to help the 
      portfolio manager make an informed trading decision.

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


    def analysis(self, knowledge) -> tuple[str, str]:
        log = super().run(knowledge=knowledge) # later use other data from the conversation log to replace the knowledge.
        # print it out:
        for speaker, text in log:
            print(f"({speaker}): {text}\n")
        return {"messages": [message], "data": data}



risk_manager = RiskManager(portfolio_agents = [aggressive_risk_manager, conservative_risk_manager, neutral_risk_manager], rounds=6)       


if __name__ == "__main__":
  result = risk_manager.analysis()
  print(result)