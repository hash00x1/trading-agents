from typing import Callable, List

from langchain.memory import ConversationBufferMemory
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from langchain.agents import AgentType, initialize_agent, load_tools

class DialogueAgent:
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: ChatOpenAI,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.model = model
        self.prefix = f"{self.name}: "
        self.reset()

    def reset(self):
        self.message_history = ["Here is the conversation so far."]

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        message = self.model.invoke(
            [
                self.system_message,
                HumanMessage(content="\n".join(self.message_history + [self.prefix])),
            ]
        )
        return message.content

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        self.message_history.append(f"{name}: {message}")
class DialogueAgentWithTools(DialogueAgent):
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: ChatOpenAI,
        tool_names: List[str],
        **tool_kwargs,
    ) -> None:
        super().__init__(name, system_message, model)
        self.tools = load_tools(tool_names, **tool_kwargs)

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        agent_chain = initialize_agent(
            self.tools,
            self.model,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=ConversationBufferMemory(
                memory_key="chat_history", return_messages=True
            ),
        )
        message = AIMessage(
            content=agent_chain.run(
                input="\n".join([self.system_message.content] + self.message_history + [self.prefix])
            )
        )

        return message.content

# Function to alternate between Bullish and Bearish Researchers
def select_next_speaker(step: int, agents: List[DialogueAgentWithTools]) -> int:
    return (step) % len(agents)  # Alternating speakers


class DialogueSimulatorAgent:
# Change this so that it could be reused with following functions:
# select rounds of debate.
# support different 
    def __init__(
        self,
        agents: List[DialogueAgent],
        # selection_function: Callable[[int, List[DialogueAgent]], int],
        rounds: int = 6,
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = select_next_speaker
        self.rounds = rounds

    def reset(self):
        for agent in self.agents:
            agent.reset()
        self._step = 0

    def inject(self, name: str, message: str):
        """
        Initiates the conversation with a {message} from {name}
        """
        for agent in self.agents:
            agent.receive(name, message)

        # increment time
        self._step += 1

    def step(self) -> tuple[str, str]:
        # 1. choose the next speaker
        speaker_idx = self.select_next_speaker(self._step, self.agents)
        speaker = self.agents[speaker_idx]

        # 2. next speaker sends message
        message = speaker.send()

        # 3. everyone receives message
        for receiver in self.agents:
            receiver.receive(speaker.name, message)

        # 4. increment time
        self._step += 1

        return speaker.name, message
    
    def run(
            self,
            initial_message: str,
            moderator_name: str = "Moderator",
            ) -> List[tuple[str, str]]:
        """
        Resets, injects the initial message, and runs the conversation
        """
        self.reset()
        log: List[tuple[str, str]] = []

        # kick things off
        self.inject(moderator_name, initial_message)
        log.append((moderator_name, initial_message))

        for _ in range(self.rounds):
            name, message = self.step()
            log.append((name, message))
        return log
    
