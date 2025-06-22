from typing import Annotated
from langchain_core.tools import tool
from typing import Annotated
import base_workflow.tools.openai_news_crawler as openai_news_crawler


class Toolkit:
    #_config = DEFAULT_CONFIG.copy()

    # @classmethod
    # def update_config(cls, config):
    #     """Update the class-level configuration."""
    #     cls._config.update(config)

    # @property
    # def config(self):
    #     """Access the configuration."""
    #     return self._config

    # def __init__(self, config=None):
    #     if config:
    #         self.update_config(config)


    @staticmethod
    @tool
    def get_crypto_social_news_openai(
        ticker: Annotated[str, "the company's ticker"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given stock by using OpenAI's news API.
        Args:
            ticker (str): Ticker of a company. e.g. AAPL, TSM
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the company on the given date.
        """

        openai_news_results = openai_news_crawler.get_crypto_social_news_openai(ticker, curr_date)

        return openai_news_results

    @staticmethod
    @tool
    def get_crypto_global_news_openai(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using OpenAI's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        openai_news_results = openai_news_crawler.get_crypto_global_news_openai(curr_date)

        return openai_news_results
