from typing import Callable, List
import os
import sys
from langchain.memory import ConversationBufferMemory
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from base_workflow.utils.debate_agent import DialogueAgent, DialogueSimulatorAgent, DialogueAgentWithTools

if __name__ == "__main__":        
    names = {
        "Bearish_researcher": ["arxiv", "ddg-search", "wikipedia"],
        "Bullish_researcher": ["arxiv", "ddg-search", "wikipedia"],
    }
    topic = "The current tendency of Apple Inc.'s stock price"
    word_limit = 50  # word limit for task brainstorming

    conversation_description = f"""Here is the topic of conversation: {topic}
    The participants are: {', '.join(names.keys())}"""

    agent_descriptor_system_message = SystemMessage(
        content="You can add detail to the description of the conversation participant."
    )


    def generate_agent_description(name):
        agent_specifier_prompt = [
            agent_descriptor_system_message,
            HumanMessage(
                content=f"""{conversation_description}
                Please reply with a creative description of {name}, in {word_limit} words or less. 
                Speak directly to {name}.
                Give them a point of view.
                Do not add anything else."""
            ),
        ]
        agent_description = ChatOpenAI(temperature=1.0)(agent_specifier_prompt).content
        return agent_description


    agent_descriptions = {name: generate_agent_description(name) for name in names}

    for name, description in agent_descriptions.items():
        print(description)

    def generate_system_message(name, description, tools):
        return f"""{conversation_description}
        
                Your name is {name}.

                Your description is as follows: {description}

                Your goal is to persuade your conversation partner of your point of view.

                DO look up information with your tool to refute your partner's claims.
                DO cite your sources.

                DO NOT fabricate fake citations.
                DO NOT cite any source that you did not look up.

                Do not add anything else.

                Stop speaking the moment you finish speaking from your perspective.
                """


    agent_system_messages = {
        name: generate_system_message(name, description, tools)
        for (name, tools), description in zip(names.items(), agent_descriptions.values())
    }

    for name, system_message in agent_system_messages.items():
        print(name)
        print(system_message)

    topic_specifier_prompt = [
        SystemMessage(content="You can make a topic more specific."),
        HumanMessage(
            content=f"""{topic}
            
            You are the moderator.
            Please make the topic more specific.
            Please reply with the specified quest in {word_limit} words or less. 
            Speak directly to the participants: {*names,}.
            Do not add anything else."""
        ),
    ]
    specified_topic = ChatOpenAI(temperature=1.0)(topic_specifier_prompt).content # check if this part should be added to the class

    print(f"Original topic:\n{topic}\n")
    print(f"Detailed topic:\n{specified_topic}\n")

    # we set `top_k_results`=2 as part of the `tool_kwargs` to prevent results from overflowing the context limit
    # here the two agents are set.
    agents = [
        DialogueAgentWithTools(
            name=name,
            system_message=SystemMessage(content=system_message),
            model=ChatOpenAI(model="gpt-4", temperature=0.2),
            tool_names=tools,
            top_k_results=2,
        )
        for (name, tools), system_message in zip(
            names.items(), agent_system_messages.values()
        )
    ]

    def select_next_speaker(step: int, agents: List[DialogueAgent]) -> int:
        idx = (step) % len(agents)
        return idx

    max_iters = 6
    n = 0

    simulator = DialogueSimulatorAgent(agents=agents)
    simulator.reset()
    simulator.inject("Moderator", specified_topic)
    print(f"(Moderator): {specified_topic}")
    print("\n")

    while n < max_iters:
        name, message = simulator.step()
        print(f"({name}): {message}")
        print("\n")
        n += 1