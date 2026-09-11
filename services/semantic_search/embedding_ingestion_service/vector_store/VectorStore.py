from abc import ABC, abstractmethod
from data_models import DocumentChunk
import numpy as np


class VectorStore(ABC):
    """
    Interface representing a store for vector embeddings.
    """

    @abstractmethod
    def insert(
        self,
        chunks: list[DocumentChunk],
        embeddings: np.ndarray
    ) -> None:
        'Insert text chunks, their metadata and embeddings into the vector store.'
        pass

    
    @abstractmethod
    def clear(self) -> None:
        """Remove all vectors from the collection."""
        pass