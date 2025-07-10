from typing import Callable, List
from langchain.memory import ConversationBufferMemory
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from typing import Optional
from langchain_core import messages
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.agents import Agent, AgentType, initialize_agent, load_tools
from base_workflow.graph.state import AgentState
from operator import add
from typing import Annotated, Sequence
from langchain.schema import BaseMessage
import operator

class DialogueAgent:
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: ChatOpenAI,
        state: AgentState,
    ) -> None:
        self.name = name
        self.system_message = system_message
        self.model = model
        self.prefix = f"{self.name}: "
        self.state = state

        self.messages_history: Annotated[Sequence[BaseMessage], operator.add] = []
        self.messages: List[str] = []

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        message = self.model.invoke(
            [
                self.system_message,
                HumanMessage(content="\n".join([str(m.content) for m in self.messages_history] + [self.prefix])),  # put in whole message history for the agents to debate
            ]
        )
        # self.messages records the messages from this dialogagent. self.messages_history records the whole message history.
        self.messages_history = operator.add(self.messages_history, [HumanMessage(content=f"{self.prefix}: {message}")])
        self.messages.append("\n" + str(message.content))
        return str(message.content)

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        self.messages_history = operator.add(self.messages_history, [HumanMessage(content=f"{name}: {message}")])


# for future devolop
class DialogueAgentWithTools(DialogueAgent):
    def __init__(
        self,
        name: str,
        system_message: SystemMessage,
        model: ChatOpenAI,
        state: AgentState,
        tool_names: List[str],
        **tool_kwargs,
    ) -> None:
        super().__init__(name, system_message, model, state)
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
            handle_parsing_errors=True
        )
        message = AIMessage(
            content=agent_chain.run(
                input = "\n".join([str(self.system_message.content)] + [str(m.content) for m in self.messages_history]+ [self.prefix])
            )
        )

        self.messages_history = operator.add(self.messages_history, [HumanMessage(content=f"{self.prefix}: {message}")])
        self.messages.append("\n" + str(message.content))

        return str(message.content)

# Function to alternate between Bullish and Bearish Researchers
def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:
    return (step) % len(agents)  # Alternating speakers


class DialogueSimulatorAgent:
    def __init__(
        self,
        agents: list[DialogueAgent],
        rounds: int = 6,
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = select_next_speaker
        self.rounds = rounds

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
            state: Optional[AgentState] = None,
            ) -> List[tuple[str, str]]:
        """
        Resets, injects the initial message, and runs the conversation
        """
        self._step = 0
        log: List[tuple[str, str]] = []

        # kick things off
        log.append(("previous knowledge", knowledge))

        for _ in range(self.rounds):
            name, message = self.step()
            log.append((name, message))
        return log
    
#######################################
# testing usage
# for testing purposes please uncomment the following lines and run the code
######################################
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
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
#test usage
llm = ChatOpenAI(model="gpt-4o")
# bearish_researcher_tools = ["arxiv", "ddg-search", "wikipedia"]
bearish_researcher_system_message = """
You are a Bearish Researcher. 
Your role is to focus on potential downsides, risks, and unfavorable market signals. 
You should argue that investments in certain assets could have negative outcomes due to market volatility, economic downturns, or poor growth potential. Provide cautionary insights to convince others not to invest or to consider risk management strategies.
"""
bearish_researcher = DialogueAgent(
    name="bearish Researcher",
    system_message=SystemMessage(content=bearish_researcher_system_message),
    model=llm,
    # tool_names=bearish_researcher_tools,
    state = test_state
)    

bullish_researcher_tools = ["arxiv", "ddg-search", "wikipedia"]
bullish_researcher_system_message = """
You are a Bullish Researcher. Your role is to highlight positive indicators, growth potential, and favorable market conditions. 
You advocate for investment opportunities by emphasizing high growth, strong fundamentals, and positive market trends. 
You should encourage others to initiate or continue positions in certain assets.
"""
bullish_researcher = DialogueAgent(
    name="Bullish Researcher",
    system_message=SystemMessage(content=bullish_researcher_system_message),
    model=llm,
    # tool_names=bullish_researcher_tools,
    state = test_state
)

if __name__ == '__main__':

    test_simulator = DialogueSimulatorAgent(
        agents=[bullish_researcher, bearish_researcher],
    )

    # run the full dialogue:
    transcript = test_simulator.run("")

    # print it out:
    for speaker, text in transcript:
        print(f"({speaker}): {text}\n")