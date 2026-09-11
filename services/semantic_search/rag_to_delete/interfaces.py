from typing import Protocol
import numpy as np

from data_models import SearchResult


class AnswerModel(Protocol):
    """
    Interface for a model that generates an answer from a prompt.
    """

    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 100,
    ) -> str:
        """
        Generate text from a prompt.
        """
        pass


class SemanticSearchTool(Protocol):
    """
    Interface for a semantic-search tool.

    The concrete implementation can use MCP, HTTP, gRPC, etc.
    """

    async def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[SearchResult]:
        """
        Search for documents semantically similar to the query.
        """
        pass