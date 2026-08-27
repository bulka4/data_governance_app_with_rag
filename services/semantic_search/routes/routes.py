'''
Ray Serve application with routes for a semantic search. To be deployed using Ray Serve (the KubeRay operator on Kubernetes).
'''

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve
from pymilvus import connections, Collection
import os
import traceback

from functions import EmbeddingModel



# ================= Parameters =================
# Path with the saved ONNX model to use for generating sentence embeddings
model_path = os.getenv('MODEL_PATH') or '../ml_models/all-MiniLM-L6-v2'


# We are using an index type of the IVF family in this collection. The 'nprobe' parameter specifies a number of 
# clusters (buckets) we are going to search through when looking for the most similar vectors.
nprobe = 10
# IP address or DNS name of the Milvus db where we store documents used for semantic search.
milvus_host = os.getenv('MILVUS_HOST') or 'localhost'
# Name of the collection in the Milvus db with documents used for semantic search.
milvus_collection = os.getenv('MILVUS_COLLECTION_NAME') or 'my_docs'
# Name of the field in the Collection which holds vector embeddings.
embedding_field_name = os.getenv('EMBEDDING_FIELD_NAME') or 'embedding'
# Name of the field in the Collection which holds document text.
text_field_name = os.getenv('TEXT_FIELD_NAME') or 'text'




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
        self
        ,model_path
        ,milvus_host
        ,milvus_collection
    ):
        # Prepare a model for generating embeddings
        self.model = EmbeddingModel(
            download_model=False,
            model_name=None,
            model_path=model_path,
            batch_size=32,
        )

        # ----- Connect to Milvus -----
        connections.connect("default", host=milvus_host, port="19530")
        self.collection = Collection(milvus_collection)
        self.collection.load()


    @app.get("/search")
    async def ask(self, query: str, top_k: int = 3) -> dict:
        """
        Function for semantic search.
        """
        # embedding for the user's query
        sentence_embedding = self.model.run(query)

        # Find documents in the Milvus vector database similar to the user's query 
        results = self.collection.search(
            data=sentence_embedding,
            anns_field=embedding_field_name,
            # param={"metric_type": "COSINE", "params": {"nprobe": nprobe}},
            param={"params": {"nprobe": nprobe}},
            limit=top_k,
            output_fields=[text_field_name]
        )

        # Return text found in the vector database
        return [result.entity.get(text_field_name) for result in results[0]]

semantic_search_service = RAGService.bind(
    model_path=model_path
    ,milvus_host=milvus_host
    ,milvus_collection=milvus_collection
)