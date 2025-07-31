# llm_factory.py

from typing import Optional
from langchain_openai import ChatOpenAI


def get_llm(
	variant: Optional[Variant] = None,
	*,
	temperature: Optional[float] = None,
) -> ChatOpenAI:
	"""
	统一返回 ChatOpenAI 实例；支持基线切换与缓存复用。
	- variant: "4o" 或 "4.1"，默认读环境变量 LLM_BASELINE。
	- temperature: 不传则用默认。
	"""
	v = variant or DEFAULT_VARIANT
	model_name = _resolve_model(v)
	temp = DEFAULT_TEMPERATURE if temperature is None else temperature
	return ChatOpenAI(model=model_name, temperature=temp)
