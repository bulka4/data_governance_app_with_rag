"""
- In this script we prepare the MCP tool for semantic search. 
- The tool is asynchronous.
- It uses an existing REST API server that provides the `/search` endpoint for performing the semantic search.
- It will listen at 'http://<hostname>:8000/mcp/'
"""

import os
from typing import List

import httpx
from fastmcp import FastMCP


# ---------------------------------------------
# Parameters 
# ---------------------------------------------
# URL used to make REST API calls for semantic search
SEMANTIC_SEARCH_URL = os.getenv(
    "SEMANTIC_SEARCH_URL",
    "http://semantic-search-rayservice-head:8000/search",
)

# When we use 0.0.0.0, then this process will listen on all network intefaces so processes from other servers
# will be able to connect. If we use 127.0.0.1 instead, then it will listen only on the loopback interface and we
# will be able to connect only from the same server.
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))


# ---------------------------------------------
# MCP Server 
# ---------------------------------------------
mcp = FastMCP("semantic-search")


# ---------------------------------------------
# MCP Tool
# ---------------------------------------------
@mcp.tool()
async def search_docs(query: str, top_k: int = 3) -> List[dict]:
    """
    Search the document collection using semantic similarity.

    Args:
        query: User's natural-language search query.
        top_k: Number of documents to retrieve.
    """

    async with httpx.AsyncClient() as client:
        response = await client.get(
            SEMANTIC_SEARCH_URL,
            params={
                "query": query,
                "top_k": top_k,
            },
        )

    response.raise_for_status()

    return response.json()


# ----- Run Server -----
if __name__ == "__main__":
    # Start the MCP server using the HTTP Transport. This will enable clients to connect over HTTP.
    mcp.run(
        transport="http",
        host=MCP_HOST,
        port=MCP_PORT,
    )