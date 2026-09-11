'''
- Ray Serve application with routes for a semantic search. 
- To be deployed using the Ray Serve (the KubeRay operator on Kubernetes or by running the `serve run` command in a terminal).
- It performs semantic search by searching through a specific Milvus collection
'''

import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve

import os
import traceback

from rag_workflow import RAGWorkflow
from interfaces import EmbeddingModel


# ================= Parameters =================

# Whether or not to download a new model for generating embeddings from the Hugging Face (if we don't provide it,
# we need to have a model saved already and provide a path to it using the model_path parameter)
download_model = os.getenv("DOWNLOAD_MODEL") == "True"

# Path with the saved ONNX model to use for generating sentence embeddings
model_path = os.getenv("MODEL_PATH") or "/app/ml_models/all-MiniLM-L6-v2"

model_name = None
# URL of the MCP server providing a tool for semantic search
mcp_server_url = os.getenv('MCP_SERVER_URL')
# name of the MCP tool for semantic search to use
semantic_search_tool = os.getenv('SEMANTIC_SEARCH_TOOL')




# We are using an index type of the IVF family in this collection. The 'nprobe' parameter specifies a number of 
# clusters (buckets) we are going to search through when looking for the most similar vectors.
nprobe = 10

# IP address or DNS name of the Milvus db where we store documents used for semantic search.
milvus_host = os.getenv("MILVUS_HOST") or "localhost"

# Name of the collection in the Milvus db with documents used for semantic search.
milvus_collection = os.getenv("MILVUS_COLLECTION_NAME") or "my_docs"

# Name of the field in the milvus collection which holds vector embeddings.
embedding_field_name = os.getenv("EMBEDDING_FIELD_NAME") or "embedding"

# Name of the field in the milvus collection which holds metadata
metadata_field_name = os.getenv("METADATA_FIELD_NAME") or "metadata"

# Name of the field in the milvus collection which holds a text chunk
text_field_name = os.getenv("TEXT_FIELD_NAME") or "text"

# Name of the field in metadata in the milvus collection which represents an ID of the object which documentation refers to
object_id_field_name = os.getenv("OBJECT_ID_FIELD_NAME") or "object_id"


# ================= FastAPI routes =================

app = FastAPI()

# Exception handler to see the exact error in Python code when we make a Rest API call and it doesn't work.
@app.exception_handler(Exception)
async def debug_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "trace": traceback.format_exc(),
        },
    )


# ================= Ray Serve Service =================

@serve.deployment(ray_actor_options={"num_cpus": 2})
@serve.ingress(app)
class RAGService:
    def __init__(
        self,
        download_model,
        model_name,
        model_path,
    ):
        # Prepare an object for generating answers
        self.model: EmbeddingModel = EmbeddingModelAdapter(
            download_model=download_model,
            model_name=model_name,
            model_path=model_path,
            batch_size=32,
        )
        
        self.rag_workflow = RAGWorkflow(
            answer_model=self.model,
            mcp_server_url=mcp_server_url,
        )


    @app.get("/ask")
    async def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> str:
        """
        Generate an answer using the RAG system. This function returns a dictionary:
        {
            retrieved_docs: <retrieved documents relevant to the question>
            ,answer: <answer to the question>
        }
        """
        final_state = asyncio.run(self.rag_workflow.answer(query))

        print("Retrieved Docs:", final_state["retrieved_docs"])
        print("Final Answer:", final_state["answer"])
        
        return {
            'retrieved_docs': final_state["retrieved_docs"],
            'answer': final_state["answer"],
        }


semantic_search_service = RAGService.bind(
    download_model=download_model,
    model_name=model_name,
    model_path=model_path,
)