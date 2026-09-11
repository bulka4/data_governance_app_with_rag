import httpx
import asyncio
from typing import List

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def semantic_search_api(
    SEMANTIC_SEARCH_URL,
    query,
    top_k,
) -> List[dict]:
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


# response = asyncio.run(semantic_search_api(
#     SEMANTIC_SEARCH_URL = 'http://rag-rayservice-head:8000/search',
#     query = 'customer',
#     top_k = 3,
# ))
# print(response)




async def call_mcp_tool(
    mcp_server_url,
    tool_name,
    query,
    top_k,
):
    transport = StreamableHttpTransport(
        url=mcp_server_url
    )

    client = Client(transport)

    async with client:
        result = await client.call_tool(
            tool_name,
            {
                "query": query,
                "top_k": top_k,
            },
        )

    return result


response = asyncio.run(call_mcp_tool(
    mcp_server_url='http://mcp:8000/mcp/',
    tool_name='search_docs',
    query='cusomter',
    top_k=3
))
print(response.structured_content['result'][0]['object_id'])