from dataclasses import dataclass
from typing import TypedDict

# A result of semantic search (searching through a vector store)
@dataclass
class SearchResult:
    object_id: int              # ID of the document (taken from the database documentation database)
    text_chunk: str             # One text chunk from the document
    similarity_score: float     # Similarity score for this text chunk and the given query


# LangGraph workflow state (containing graph input parameters, documents retrieved using semantic search and generated answer)
@dataclass
class RAGState(TypedDict, total=False):
    # query and top_k are input parameters for the graph
    query: str
    top_k: int
    # documents retrieved using semantic search
    retrieved_docs: list[SearchResult]
    # generated answer
    answer: str


@dataclass
class AskRequest:
    query: str
    top_k: int = 3


@dataclass
class AskResponse:
    answer: str
    retrieved_docs: list[SearchResult]