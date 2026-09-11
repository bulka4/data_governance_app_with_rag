# api.py

import os

from fastapi import FastAPI
from ray import serve

from data_models import AskRequest, AskResponse
from interfaces import AnswerModel, SemanticSearchTool
from interface_implementations.MCPSemanticSearchTool import MCPSemanticSearchTool
from interface_implementations.TransformersAnswerModel import TransformersAnswerModel
from RAGWorkflow import RAGWorkflow


# ========================================================================================
# Parameters
# ========================================================================================

# URL of the MCP server to use for semantic search
mcp_server_url=os.environ["MCP_SERVER_URL"]
# Name of the MCP tool for semantic search to use
semantic_search_tool=os.environ["SEMANTIC_SEARCH_TOOL"]

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
download_model=os.getenv("DOWNLOAD_MODEL") == "True"
model_name=os.getenv("MODEL_NAME")
model_path=os.environ["MODEL_PATH"]



# ========================================================================================
# FastAPI routes & Ray Serve app
# ========================================================================================
app = FastAPI()


@serve.deployment
@serve.ingress(app)
class RAGService:
    def __init__(self):
        # Object for performing semantic search
        self.semantic_search: SemanticSearchTool = MCPSemanticSearchTool(
            mcp_server_url=mcp_server_url,
            semantic_search_tool=semantic_search_tool,
        )

        # Object for using a model for generating an answer
        self.answer_model: AnswerModel = TransformersAnswerModel(
            download_model=download_model,
            model_name=model_name,
            model_path=model_path,
        )

        # Object for running a RAG workflow (retrieve relevant documents and generate an answer based on them)
        self.rag_workflow = RAGWorkflow(
            semantic_search=self.semantic_search,
            answer_model=self.answer_model,
        )

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

        return await self.rag_workflow.answer(
            query=request.query,
            top_k=request.top_k,
        )


rag_service = RAGService.bind()