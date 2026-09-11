from typing import Protocol
import numpy as np

from data_models import SearchResult

class EmbeddingModel(Protocol):
    '''
    Interface for generating vector embeddings using a ML model.
    '''
    def run(self, text: str) -> np.ndarray:
        ...

class VectorStore(Protocol):
    '''
    Interface for performing a vector search in a vector database (looking for similar vector embeddings).
    '''
    def search(
        self,
        embedding: np.ndarray,
        top_k: int
    ) -> list[SearchResult]:
        ...


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