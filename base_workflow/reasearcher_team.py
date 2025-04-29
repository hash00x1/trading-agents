from typing import List
from base_workflow.utils.debate_agent import DialogueSimulatorAgent, DialogueAgentWithTools
from base_workflow.agents import bearish_researcher, bullish_researcher

# # Function to alternate between Bullish and Bearish Researchers
# def select_next_speaker(step: int, agents: List[DialogueAgentWithTools]) -> int:
#     return (step) % len(agents)  # Alternating speakers

# # Conversation Simulating initialization
# simulator = DialogueSimulator(
#     agents=[bullish_researcher, bearish_researcher],
#     # selection_function=select_next_speaker
# )
# simulator.reset()

# # Start the conversation with the initial topic
# initial_message = "Let's discuss the potential of technology stocks in the current market."
# simulator.inject("Moderator", initial_message)
# print(f"(Moderator): {initial_message}\n")

# # TODO: move this into the debate agent utils.
# max_iters = 6
# for _ in range(max_iters):
#     name, message = simulator.step()
#     print(f"({name}): {message}\n")


simulator = DialogueSimulatorAgent(
    agents=[bullish_researcher, bearish_researcher],
)

# run the full dialogue:
transcript = simulator.run(
    initial_message="Let's discuss the potential of technology stocks in the current market."
)


# print it out:
for speaker, text in transcript:
    print(f"({speaker}): {text}\n")