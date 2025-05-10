from typing import Callable, List

from langchain.memory import ConversationBufferMemory
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from langchain.agents import Agent, AgentType, initialize_agent, load_tools
from base_workflow.state import AgentState
from operator import add

# For refering use: define agent state
# class AgentState(TypedDict):
#     messages: Annotated[Sequence[BaseMessage], operator.add]
#     data: Annotated[dict[str, any], merge_dicts]
#     metadata: Annotated[dict[str, any], merge_dicts]

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
        self.state: AgentState = {
            "messages": [],
            "data": {},
            "metadata": {},
        }

    def send(self) -> str:
        """
        Applies the chatmodel to the message history
        and returns the message string
        """
        message = self.model.invoke(
            [
                self.system_message,
                #HumanMessage(content="\n".join(self.message_history + [self.prefix])),
                HumanMessage(content="\n".join(add(self.state["messages"], [self.prefix]))),
            ]
        )
        #check if this part could be correct
        return str(message.content)

    def receive(self, name: str, message: str) -> None:
        """
        Concatenates {message} spoken by {name} into message history
        """
        # self.message_history.append(f"{name}: {message}")
        self.state["messages"].append(f"{name}: {message}")

        
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
                # input="\n".join([self.system_message.content] + self.message_history + [self.prefix])
                input="\n".join([self.system_message.content] + add(self.state["messages"], [self.prefix]))
            )
        )

        return str(message.content)

# Function to alternate between Bullish and Bearish Researchers
def select_next_speaker(step: int, agents: List[DialogueAgentWithTools]) -> int:
    return (step) % len(agents)  # Alternating speakers


class DialogueSimulatorAgent:
# Change this so that it could be reused with following functions:
# select rounds of debate.
# support different 
    def __init__(
        self,
        agents: list[DialogueAgentWithTools],
        # selection_function: Callable[[int, List[DialogueAgent]], int],
        rounds: int = 6,
    ) -> None:
        self.agents = agents
        self._step = 0
        self.select_next_speaker = select_next_speaker
        self.rounds = rounds

    # def reset(self):
    #     for agent in self.agents:
    #         agent.reset()
    #     self._step = 0

    def inject(self, name: str):
        """
        Initiates the conversation with a {message} from {name}
        """
        message = str(self.state["messages"])
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
            knowledge: str,
            ) -> List[tuple[str, str]]:
        """
        Resets, injects the initial message, and runs the conversation
        """
        for agent in self.agents:
            agent.reset()
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
#######################################
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import SystemMessage

# #test usage
# llm = ChatOpenAI(model="gpt-4o")
# bearish_researcher_tools = ["arxiv", "ddg-search", "wikipedia"]
# bearish_researcher_system_message = """
# You are a Bearish Researcher. 
# Your role is to focus on potential downsides, risks, and unfavorable market signals. 
# You should argue that investments in certain assets could have negative outcomes due to market volatility, economic downturns, or poor growth potential. Provide cautionary insights to convince others not to invest or to consider risk management strategies.
# """
# bearish_researcher = DialogueAgentWithTools(
#     name="bearish Researcher",
#     system_message=SystemMessage(content=bearish_researcher_system_message),
#     model=llm,
#     tool_names=bearish_researcher_tools
# )    

# bullish_researcher_tools = ["arxiv", "ddg-search", "wikipedia"]
# bullish_researcher_system_message = """
# You are a Bullish Researcher. Your role is to highlight positive indicators, growth potential, and favorable market conditions. 
# You advocate for investment opportunities by emphasizing high growth, strong fundamentals, and positive market trends. 
# You should encourage others to initiate or continue positions in certain assets.
# """
# bullish_researcher = DialogueAgentWithTools(
#     name="Bullish Researcher",
#     system_message=SystemMessage(content=bullish_researcher_system_message),
#     model=llm,
#     tool_names=bullish_researcher_tools
# )

# if __name__ == '__main__':

#     test_simulator = DialogueSimulatorAgent(
#         agents=[bullish_researcher, bearish_researcher],
#     )

#     # run the full dialogue:
#     transcript = test_simulator.run(
#         initial_message="Let's discuss the potential of technology stocks in the current market."
#     )


#     # print it out:
#     for speaker, text in transcript:
#         print(f"({speaker}): {text}\n")