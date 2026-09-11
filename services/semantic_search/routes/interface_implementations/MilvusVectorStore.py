'''
Implementation of the VectorStore interface for Milvus database.
'''

from data_models import SearchResult
from pymilvus import MilvusClient
import numpy as np

class MilvusVectorStore():
    def __init__(
        self,
        host: str,
        collection: str,
        embedding_field_name: str,
        metadata_field_name: str,
        text_field_name: str,
        object_id_field_name: str,
        nprobe: int,
    ):
        self.client = MilvusClient(
            uri=f"http://{host}:19530"
        )

        self.collection = collection
        self.embedding_field_name = embedding_field_name
        self.metadata_field_name = metadata_field_name
        self.text_field_name = text_field_name
        self.object_id_field_name = object_id_field_name
        self.nprobe = nprobe

        self.client.load_collection(
            collection_name=self.collection
        )

    def search(
        self,
        embedding: np.ndarray,
        top_k: int
    ) -> list[SearchResult]:

        results = self.client.search(
            collection_name=self.collection,
            data=embedding.tolist(),
            anns_field=self.embedding_field_name,
            limit=top_k,
            output_fields=[
                self.metadata_field_name,
                self.text_field_name
            ],
            search_params={
                "params": {
                    "nprobe": self.nprobe
                }
            },
        )

        return [
            SearchResult(
                object_id=result.entity
                    .get(self.metadata_field_name)
                    .get(self.object_id_field_name),
                text_chunk=result.entity.get(self.text_field_name),
                similarity_score=result.get("distance"),
            )
            for result in results[0]
        ]