"""
In this script we prepare the MCP tool for semantic search. It will use the Milvus db as a vector db where we will store vector 
embeddings of documents.
"""

from fastmcp import FastMCP
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer
from typing import List
import os

# ----- Parameters -----

# nprobe - We are using an index type of the IVF family in this collection. The 'nprobe' parameter specifies a number of 
#          clusters (buckets) we are going to search through when looking for the most similar vectors.
# milvus_host - IP address or DNS name of the Milvus db where we store documents used for semantic search.
# milvus_collection - Name of the collection in the Milvus db with documents used for semantic search.
# embedding_field_name - Name of the field in the Collection which holds vector embeddings.
# text_field_name - Name of the field in the Collection which holds document text.
nprobe = 10
milvus_host = os.getenv('MILVUS_HOST') or 'localhost'
milvus_collection = os.getenv('MILVUS_COLLECTION_NAME') or 'my_docs'
embedding_field_name = os.getenv('EMBEDDING_FIELD_NAME') or 'embedding'
text_field_name = os.getenv('TEXT_FIELD_NAME') or 'text'

# ----- MCP Server -----
mcp = FastMCP("milvus-search")

# ----- Connect to Milvus -----
# As host we provide here name of the service in Docker Compose running the Milvus db.
connections.connect("default", host=milvus_host, port="19530")
collection = Collection(milvus_collection)
collection.load()

# ----- Embedding model -----
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ----- MCP Tool -----
@mcp.tool()
def search_docs(query: str, top_k: int = 3) -> List[str]:
    """
    Retrieve relevant documents from Milvus using embeddings.
    """
    query_emb = embedder.encode([query]).tolist()

    results = collection.search(
        data=query_emb,
        anns_field=embedding_field_name,
        # param={"metric_type": "COSINE", "params": {"nprobe": nprobe}},
        param={"params": {"nprobe": nprobe}},
        limit=top_k,
        output_fields=[text_field_name]
    )
    
    return [result.entity.get(text_field_name) for result in results[0]]


# ----- Run Server -----
if __name__ == "__main__":
    # Start the MCP server using the HTTP Transport. This will enable clients to connect over HTTP.
    mcp.run(
        transport="http"
        # When we use 0.0.0.0, then this process will listen on all network intefaces so processes from other servers
        # will be able to connect. If we use 127.0.0.1 instead, then it will listen only on the loopback interface and we
        # will be able to connect only from the same server.
        ,host="0.0.0.0"
        ,port=8000
    )