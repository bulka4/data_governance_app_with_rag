from dataclasses import dataclass
from typing import TypedDict

# A result of searching through a vector store
@dataclass
class SearchResult:
    object_id: int              # ID of the document (taken from the database documentation database)
    text_chunk: str             # One text chunk from the document
    similarity_score: float     # Similarity score for this text chunk and the given query


@dataclass
class RAGState(TypedDict, total=False):
    query: str
    top_k: int
    retrieved_docs: list[SearchResult]
    answer: str


@dataclass
class AskRequest:
    query: str
    top_k: int = 3


@dataclass
class AskResponse:
    answer: str
    retrieved_docs: list[SearchResult]