from dataclasses import dataclass
from typing import Any

@dataclass
class DocumentChunk:
    """
    A chunk of documentation that will become one vector embedding in the vector database.
    """

    text: str
    object_type: str    # "table" or "column"
    object_name: str    # name of the table or column
    object_id: Any      # ID of the table document (taken from the database documentation database)
    chunk_id: int       # ID of the chunk that belongs to the document

    @property
    def metadata(self) -> dict[str, Any]:
        'Property for getting metadata as JSON so it can be inserted into a field in a vector store collection.'
        return {
            "object_type": self.object_type,
            "object_name": self.object_name,
            "object_id": self.object_id,
            "chunk_id": self.chunk_id
        }