# # Helper function to create a node for a given agent
# from langchain.schema import AIMessage
# from base_workflow.agents import default_agent
# from base_workflow.state import AgentState


# def agent_node(state: AgentState) -> AgentState:
# 	result = default_agent.invoke({'messages': state['messages']})
# 	# We convert the agent output into a format that is suitable to append to the global state
# 	if not isinstance(result, AIMessage):
# 		raise ValueError('Agent did not return AIMessage')
# 	return {'messages': [result]}
