from abc import ABC, abstractmethod
import numpy as np

class EmbeddingModel(ABC):
    """
    Interface representing a model for converting text into vector embeddings.
    """

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Returns a matrix of a shape = (number_of_texts, embedding_dimension)
        """
        pass