from langchain.schema import AIMessage
from base_workflow.state import AgentState


def router(state: AgentState):
	# This is the router
	messages = state['messages']
	last_message = messages[-1]
	if isinstance(last_message, AIMessage) and last_message.tool_calls:
		# route to tool call
		return 'call_tool'
	if 'FINAL ANSWER' in last_message.content:
		# finish execution
		return 'end'
	return 'continue'
