from langchain_openai import ChatOpenAI

LLM_MODEL_NAME = 'gpt-4.1-mini'  # gpt-4.1-nano


def get_llm():
	return ChatOpenAI(model=LLM_MODEL_NAME, temperature=0)


if __name__ == '__main__':
	llm = get_llm()
	response = llm.invoke('Hello')
	print(response)
