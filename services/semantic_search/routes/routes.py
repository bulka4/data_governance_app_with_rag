'''
- Ray Serve application with routes for a semantic search and answering questions using a RAG system.
- To be deployed using the Ray Serve (the KubeRay operator on Kubernetes or by running the `serve run` command in a terminal).
- Semantic search is performed by searching through a specific Milvus collection
'''

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve

import os
import traceback

from interfaces import EmbeddingModel, VectorStore
from data_models import SearchResult, AskRequest, AskResponse
from interface_implementations.TransformersEmbeddingModel import TransformersEmbeddingModel
from interface_implementations.MilvusVectorStore import MilvusVectorStore

from interfaces import AnswerModel, SemanticSearchTool
from interface_implementations.MCPSemanticSearchTool import MCPSemanticSearchTool
from interface_implementations.TransformersAnswerModel import TransformersAnswerModel
from RAGWorkflow import RAGWorkflow


# ================= Parameters =================

# - download_model
#     - When set to False, it will load already saved ONNX model
#     - When set to True, it will download a new model from Hugging Face if it doesn't exist yet and save it in the ONNX format 
#         using optimum-cli
# - model_name, model_path
#     - when download_model = True, then we need to provide both arguments:
#         - model_name - Name of the model to download using optimum-cli, e.g. sentence-transformers/all-MiniLM-L6-v2
#         - model_path - Where to save the downloaded model
#     - when download_model = False, then we need to provide only the model_path argument specifying the path of the
#         ONNX model to load

# Parameters for the model for generating embeddings (download_model, model_name, model_path)
download_embedding_model = os.getenv("DOWNLOAD_EMBEDDING_MODEL") == "True"
embedding_model_name = os.getenv('EMBEDDING_MODEL_NAME') or None
embedding_model_path = os.getenv("EMBEDDING_MODEL_PATH") or "/app/ml_models/embeddings/all-MiniLM-L6-v2"

# Parameters for the model for generating answers (download_model, model_name, model_path)
download_answer_model = os.getenv("DOWNLOAD_ANSWER_MODEL") == "True"
answer_model_name = os.getenv('ANSWER_MODEL_NAME') or None
answer_model_path = os.getenv("ANSWER_MODEL_PATH") or "/app/ml_models/answer/all-MiniLM-L6-v2"


# URL of the MCP server to use for semantic search
mcp_server_url=os.environ["MCP_SERVER_URL"]
# Name of the MCP tool for semantic search to use
semantic_search_tool=os.environ["SEMANTIC_SEARCH_TOOL"]


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

        download_embedding_model,
        embedding_model_name,
        embedding_model_path,

        download_answer_model,
        answer_model_name,
        answer_model_path,

        milvus_host,
        milvus_collection,
        embedding_field_name,
        metadata_field_name,
        text_field_name,
        object_id_field_name,
        nprobe,

        mcp_server_url,
        semantic_search_tool,
    ):
        # ==============================================================================
        # Objects for semantic search
        # ==============================================================================

        # Prepare an object for generating embeddings
        self.model: EmbeddingModel = TransformersEmbeddingModel(
            download_model=download_embedding_model,
            model_name=embedding_model_name,
            model_path=embedding_model_path,
            batch_size=32,
        )

        # Prepare an object for vector search
        self.vector_store: VectorStore = MilvusVectorStore(
            host=milvus_host,
            collection=milvus_collection,
            embedding_field_name=embedding_field_name,
            metadata_field_name=metadata_field_name,
            text_field_name=text_field_name,
            object_id_field_name=object_id_field_name,
            nprobe=nprobe,
        )

        
        # ==============================================================================
        # Objects for the RAG system
        # ==============================================================================

        # Object for performing semantic search
        self.semantic_search: SemanticSearchTool = MCPSemanticSearchTool(
            mcp_server_url=mcp_server_url,
            tool_name=semantic_search_tool,
        )

        # Object for using a model for generating an answer
        self.answer_model: AnswerModel = TransformersAnswerModel(
            download_model=download_answer_model,
            model_name=answer_model_name,
            model_path=answer_model_path,
        )

        # Object for running a RAG workflow (retrieve relevant documents and generate an answer based on them)
        self.rag_workflow = RAGWorkflow(
            semantic_search=self.semantic_search,
            answer_model=self.answer_model,
        )


    @app.get("/search")
    async def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
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
        embedding = self.model.run(query)

        # Records found in the vector store with vectors similar to the embedding
        results: list[SearchResult] = self.vector_store.search(
            embedding=embedding,
            top_k=top_k,
        )

        return [
            {
                "object_id": result.object_id,
                "text_chunk": result.text_chunk,
                "similarity_score": result.similarity_score,
            }
            for result in results
        ]



    @app.post("/ask", response_model=AskResponse)
    async def ask(self, request: AskRequest) -> AskResponse:
        """
        Run the RAG workflow and return the answer and retrieved documents relevant to the question.

        Returned response will be serialized by FastAPI into JSON with the following format:
        {
            "answer": str
            "retrieved_docs": list[
                {
                    "object_id": int,
                    "text_chunk": str,
                    "similarity_score": float
                }
            ]
        }
        """

        response: AskResponse = await self.rag_workflow.answer(request)

        return response


rag_service = RAGService.bind(
    download_embedding_model=download_embedding_model,
    embedding_model_name=embedding_model_name,
    embedding_model_path=embedding_model_path,

    download_answer_model=download_answer_model,
    answer_model_name=answer_model_name,
    answer_model_path=answer_model_path,

    milvus_host=milvus_host,
    milvus_collection=milvus_collection,
    embedding_field_name=embedding_field_name,
    metadata_field_name=metadata_field_name,
    text_field_name=text_field_name,
    object_id_field_name=object_id_field_name,
    nprobe=nprobe,

    mcp_server_url=mcp_server_url,
    semantic_search_tool=semantic_search_tool,
)