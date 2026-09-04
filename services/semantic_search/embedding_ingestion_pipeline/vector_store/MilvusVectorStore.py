import numpy as np
from pymilvus import MilvusClient

from .VectorStore import VectorStore
from data_models import DocumentChunk

class MilvusVectorStore(VectorStore):
    '''
    Implementation of the VectorStore interface for the Milvus vector database.
     
    It is used to insert vector embeddings into a collection with the following fields:
        - id: INT64
        - embedding: FLOAT_VECTOR
        - text: VARCHAR
        - metadata: JSON - with fields:
            - object_type
            - object_name
            - object_id
            - chunk_id

    Before inserting embeddings, all the current embeddings in the collection are removed.

    Embeddings are generated using the `ONNXEmbeddingModel` class.
    '''

    def __init__(
        self,
        uri: str,
        collection_name: str,
        embedding_field_name: str,
        text_field_name: str,
        metadata_field_name: str,
        id_field_name: str
    ):
        self.client = MilvusClient(uri)
        self.collection_name = collection_name
        self.embedding_field_name = embedding_field_name
        self.text_field_name = text_field_name
        self.metadata_field_name = metadata_field_name
        self.id_field_name = id_field_name



    def insert(
        self,
        chunks: list[DocumentChunk],
        embeddings: np.ndarray
    ) -> None:
        'Insert text chunks, their metadata and embeddings into the vector store.'
        rows = []

        for chunk, embedding in zip(
            chunks,
            embeddings
        ):
            # The 'id' field will be auto generated in Milvus
            rows.append({
                self.embedding_field_name: embedding.tolist(),
                self.text_field_name: chunk.text,
                self.metadata_field_name: chunk.metadata
            })

        if rows:
            self.client.insert(
                collection_name=self.collection_name,
                data=rows
            )



    def clear(self) -> None:
        """Remove all records from the vector store."""
        self.client.load_collection(
            collection_name=self.collection_name
        )

        self.client.delete(
            collection_name=self.collection_name,
            filter=f"{self.id_field_name} >= 0"
        )