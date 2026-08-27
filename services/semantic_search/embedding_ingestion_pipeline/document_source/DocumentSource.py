from abc import ABC, abstractmethod
from typing import Iterator
from data_models import DocumentChunk

class DocumentSource(ABC):
    """
    Interface representing a source documentation, used to prepare text chunks from which we can create vector embeddings.
    """

    @abstractmethod
    def read_chunks(self) -> Iterator[DocumentChunk]:
        'Prepare text chunks for which embeddings will be generated.'
        pass