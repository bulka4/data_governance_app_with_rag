from pymilvus import (
    connections
    ,FieldSchema
    ,CollectionSchema
    ,DataType
    ,Collection
    ,utility
)

def create_milvus_collection(
    milvus_host: str | None = None,
    port: str = "19530",
    collection_name: str | None = None,
    id_field_name: str | None = None,
    embedding_field_name: str | None = None,
    text_field_name: str | None = None,
    metadata_field_name: str | None = None,
    embedding_dim: int = 384,
    chunk_max_length: int = 1000,
    nlist: int = 128
) -> Collection:
    """
    Create Milvus collection which will be used to store sentence embeddings for semantic search.

    Here we create a collection with the following fields with names given by arguments:
    - id_field_name:            Unique entity ID
    - embedding_field_name:     Text embedding vector
    - text_field_name:          Text for which the embedding was created
    - metadata_field_name       Additional metadata

    We create the IVF index on the embedding field.

    If a collection with the specified name already exists, it is dropped and recreated.
    """
    # ----------------------------------------------------
    # Connect to Milvus
    # ----------------------------------------------------
    connections.connect(
        alias="default",
        host=milvus_host,
        port=port,
    )

    # ----------------------------------------------------
    # Create collection schema
    # ----------------------------------------------------
    if utility.has_collection(collection_name):
        utility.drop_collection(collection_name)

    fields = [
        FieldSchema(
            name=id_field_name,
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True,
        ),
        FieldSchema(
            name=embedding_field_name,
            dtype=DataType.FLOAT_VECTOR,
            dim=embedding_dim,
        ),
        FieldSchema(
            name=text_field_name,
            dtype=DataType.VARCHAR,
            max_length=chunk_max_length,
        ),
        FieldSchema(
            name=metadata_field_name,
            dtype=DataType.JSON,
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Document chunks and their embeddings",
    )

    collection = Collection(
        name=collection_name,
        schema=schema,
    )

    # ----------------------------------------------------
    # Create vector index
    # ----------------------------------------------------
    collection.create_index(
        field_name=embedding_field_name,
        index_params={
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {
                "nlist": nlist,
            },
        },
    )

    return collection