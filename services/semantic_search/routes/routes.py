'''
- Ray Serve application with routes for a semantic search. 
- To be deployed using the Ray Serve (the KubeRay operator on Kubernetes or by running the `serve run` command in a terminal).
- It performs semantic search by searching through a specific Milvus collection
'''

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve
from pymilvus import MilvusClient
import os
import traceback

from functions import EmbeddingModel



# ================= Parameters =================
# Whether or not to download a new model for generating embeddings from the Hugging Face (if we don't provide it,
# we need to have a model saved already and provide a path to it using the model_path parameter)
download_model = os.getenv('DOWNLOAD_MODEL') == 'True'
# Path with the saved ONNX model to use for generating sentence embeddings
model_path = os.getenv('MODEL_PATH') or '/app/ml_models/all-MiniLM-L6-v2'


# We are using an index type of the IVF family in this collection. The 'nprobe' parameter specifies a number of 
# clusters (buckets) we are going to search through when looking for the most similar vectors.
nprobe = 10
# IP address or DNS name of the Milvus db where we store documents used for semantic search.
milvus_host = os.getenv('MILVUS_HOST') or 'localhost'
# Name of the collection in the Milvus db with documents used for semantic search.
milvus_collection = os.getenv('MILVUS_COLLECTION_NAME') or 'my_docs'
# Name of the field in the milvus collection which holds vector embeddings.
embedding_field_name = os.getenv('EMBEDDING_FIELD_NAME') or 'embedding'
# Name of the field in the milvus collection which holds metadata
metadata_field_name = os.getenv('METADATA_FIELD_NAME') or 'metadata'
# Name of the field in the milvus collection which holds a text chunk
text_field_name = os.getenv('TEXT_FIELD_NAME') or 'text'
# Name of the field in metadata in the milvus collection which represents an ID of the object which documentation refers to
object_id_field_name = os.getenv('OBJECT_ID_FIELD_NAME') or 'object_id'




# ================= FastAPI routes =================
app = FastAPI()

# Exception handler to see the exact error in Python code when we make a Rest API call and it doesn't work.
@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "trace": traceback.format_exc()},
    )


@serve.deployment(ray_actor_options={"num_cpus": 2})
@serve.ingress(app)
class RAGService:
    def __init__(
        self,
        model_path,
        milvus_host,
        milvus_collection,
        embedding_field_name,
        metadata_field_name,
        text_field_name,
        object_id_field_name,
        nprobe,
    ):
        # Prepare a model for generating embeddings
        self.model = EmbeddingModel(
            download_model=download_model,
            model_name=None,
            model_path=model_path,
            batch_size=32,
        )
        
        # ----- Connect to Milvus -----
        self.milvus = MilvusClient(
            uri=f"http://{milvus_host}:19530"
        )

        self.milvus_collection = milvus_collection
        self.embedding_field_name = embedding_field_name
        self.metadata_field_name = metadata_field_name
        self.text_field_name = text_field_name
        self.object_id_field_name = object_id_field_name
        self.nprobe = nprobe

        self.milvus.load_collection(
            collection_name=self.milvus_collection
        )


    @app.get("/search")
    async def ask(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Function for semantic search. It returns a list of dictionaries in the following format:
        [
            {
                'object_id': object_id_1,               # ID of the document (taken from the database documentation database)
                'text_chunk': text_chunk_1              # One text chunk from the document
                'similarity_score': similarity_score_1  # Similarity score for this text chunk and the given query
            },
            ...
        ]
        """
        # embedding for the user's query
        sentence_embedding = self.model.run(query)

        results = self.milvus.search(
            collection_name=self.milvus_collection,
            data=sentence_embedding.tolist(),
            anns_field=self.embedding_field_name,
            limit=top_k,
            output_fields=[self.metadata_field_name, self.text_field_name],
            search_params={"params": {"nprobe": self.nprobe}},
        )

        return [
            {
                'object_id': result.entity.get(self.metadata_field_name).get(self.object_id_field_name),
                'text_chunk': result.entity.get(self.text_field_name),
                'similarity_score': result.get('distance'),
            }
            for result in results[0]
        ]

semantic_search_service = RAGService.bind(
    model_path=model_path,
    milvus_host=milvus_host,
    milvus_collection=milvus_collection,
    embedding_field_name=embedding_field_name,
    metadata_field_name=metadata_field_name,
    text_field_name=text_field_name,
    object_id_field_name=object_id_field_name,
    nprobe=nprobe,
)