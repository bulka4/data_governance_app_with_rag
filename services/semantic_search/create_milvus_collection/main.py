"""
In this script we create Milvus collection which will be used to store sentence embeddings for semantic search.

Here we create a collection with the following fields with names given by environment variables:
    - ID_FIELD_NAME:            Unique entity ID
    - EMBEDDING_FIELD_NAME:     Text embedding vector
    - TEXT_FIELD_NAME:          Text for which the embedding was created
    - METADATA_FIELD_NAME       Additional metadata

We create the IVF index on the embedding field.

If a collection with the specified name already exists, it is dropped and recreated.
"""

from create_milvus_collection import create_milvus_collection
import os

# ----------------------------------------------------
# Parameters
# ----------------------------------------------------
milvus_host = os.getenv("MILVUS_HOST") 
collection_name = os.getenv("MILVUS_COLLECTION_NAME")
id_field_name = os.getenv("ID_FIELD_NAME")
embedding_field_name = os.getenv("EMBEDDING_FIELD_NAME")
text_field_name = os.getenv("TEXT_FIELD_NAME")
metadata_field_name = os.getenv("METADATA_FIELD_NAME")

collection = create_milvus_collection(
    milvus_host=milvus_host,
    port="19530",
    collection_name=collection_name,
    id_field_name=id_field_name,
    embedding_field_name=embedding_field_name,
    text_field_name=text_field_name,
    metadata_field_name=metadata_field_name,
    embedding_dim=384,
    chunk_max_length=1000,
    nlist=128
)

print("Database prepared")
