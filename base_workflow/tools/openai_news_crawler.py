from openai import OpenAI

def get_crypto_social_news_openai(crypto_name: str, curr_date: str):
    client = OpenAI()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Can you search search reliable news sources (such as CoinDesk, The Block, Bloomberg, Reuters, etc.) "
                            f"for news and discussions about {crypto_name} from 7 days before {curr_date}? "                        ),
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text


def get_crypto_global_news_openai(curr_date: str):
    client = OpenAI()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Can you search for global or macroeconomic news specifically related to cryptocurrencies "
                            f"(like regulations, market trends, institutional adoption, etc.) from 7 days before {curr_date}? "
                            f"Only include news published during that period."
                        ),
                    }
                ],
            }
        ],
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[
            {
                "type": "web_search_preview",
                "user_location": {"type": "approximate"},
                "search_context_size": "low",
            }
        ],
        temperature=1,
        max_output_tokens=4096,
        top_p=1,
        store=True,
    )

    return response.output[1].content[0].text

if __name__ == "__main__":
    # Example usage
    crypto_name = "Bitcoin"
    current_date = "2025-06-11"

    social_news = get_crypto_social_news_openai(crypto_name, current_date)
    macro_news = get_crypto_global_news_openai(current_date)

    print("Social Media News:\n", social_news)
    print("\nGlobal Crypto News:\n", macro_news)
