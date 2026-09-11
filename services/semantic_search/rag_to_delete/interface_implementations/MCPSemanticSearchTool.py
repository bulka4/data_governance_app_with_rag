from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from interfaces import SemanticSearchTool
from data_models import SearchResult


class MCPSemanticSearchTool(SemanticSearchTool):
    """
    Semantic search implementation using an MCP server.
    """
    def __init__(
        self,
        mcp_server_url: str,
        tool_name: str,
    ):
        self.mcp_server_url = mcp_server_url
        self.tool_name = tool_name



    async def search(
        self,
        ask_request: AskRequest,
    ) -> list[SearchResult]:

        transport = StreamableHttpTransport(
            url=self.mcp_server_url
        )

        client = Client(transport)

        async with client:
            result = await client.call_tool(
                self.tool_name,
                {
                    "query": ask_request.query,
                    "top_k": ask_request.top_k,
                },
            )

        return [
            SearchResult(
                object_id=item["object_id"],
                text_chunk=item["text_chunk"],
                similarity_score=item["similarity_score"],
            )
            for item in result.data
        ]