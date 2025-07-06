from base_workflow.agents import neutral_risk_manager
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import MessagesState
from typing import Literal
from base_workflow.agents import trader
from base_workflow.graph.state import AgentState
from base_workflow.nodes import technical_analyst_node
# test use
from langgraph.graph import StateGraph, MessagesState, START, END

# Using the trader agent to analyze the market.
def trader_node(state: AgentState) -> Command[None]:
    # State is used to pass messages and data between nodes, it is a global variable.
    print("state:", state)
    #trader's analysis
    result = trader.analysis(state["messages"])
    return Command(
        update={
            'messages': [
                HumanMessage(content=result, name='trader')
            ]
        },
        # goto="END"  # Replace with the actual next agent in the chain
    )

# def end_node(state: AgentState) -> Command[None]:
#     print("Reached end of the workflow.")
#     return Command()

if __name__ == "__main__":

    # Test trder node. 
    # The current design idea is that the trader acts 
    # as a control node to organize six debate processes 
    # and then produce the final report.
    workflow = StateGraph(AgentState)

    workflow.add_node("technical_analyst", technical_analyst_node)
    workflow.add_node("trader", trader_node)
    # workflow.add_node("END", end_node)
    workflow.set_entry_point("technical_analyst")
    workflow.add_edge("technical_analyst", "trader")
    research_graph = workflow.compile()
    # thinking about how to use the graph here.
    for s in research_graph.stream(
        {"messages": [("user", "Can you analysis current tendency of Apple Inc.'s stock price?")]},
        #subgraphs=True,
        {"recursion_limit": 10}):
        print(s)
        print("---")