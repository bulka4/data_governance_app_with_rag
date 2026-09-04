'''
This script:
    - Reads a documentation from the MongoDB database (all documents from a specific database and collection)
    - Converts it into embeddings
        - It uses for that a saved ONNX model or downloads a new model from Hugging Face if such a model is not saved yet
    - Clears a Milvus collection and inserts new embeddings
'''

from document_source.MongoDocumentSource import MongoDocumentSource
from embedding_model.ONNXEmbeddingModel import ONNXEmbeddingModel
from vector_store.MilvusVectorStore import MilvusVectorStore
from IngestionPipeline import IngestionPipeline

import os

def main():
    # --------------------------------------------------------
    # Parameters
    # --------------------------------------------------------
    # Parameters related to the MongoDB database with a source documentation to create embeddings for
    mongo_host = os.getenv('MONGO_HOST')
    mongo_db = os.getenv('MONGO_DB')
    mongo_collection = os.getenv('MONGO_COLLECTION')
    model_path = os.getenv('MODEL_PATH')

    # - download_model
    #     - When set to False, it will load already saved ONNX model
    #     - When set to True, it will download a new model from Hugging Face and save it in the ONNX format using optimum-cli
    # - model_name, model_path
    #     - when download_model = True, then we need to provide both arguments:
    #         - model_name - Name of the model to download using optimum-cli, e.g. sentence-transformers/all-MiniLM-L6-v2
    #         - model_path - Where to save the downloaded model
    #     - when download_model = False, then we need to provide only the model_path argument specifying the path of the
    #         ONNX model to load
    download_model = os.getenv('DOWNLOAD_MODEL') == 'True'
    model_name = os.getenv('MODEL_NAME')
    model_path = os.getenv('MODEL_PATH')

    # Parameters related to Milvus collection where to insert the embeddings to
    milvus_host = os.getenv("MILVUS_HOST") 
    milvus_collection = os.getenv("MILVUS_COLLECTION_NAME")
    milvus_embedding_field_name = os.getenv("EMBEDDING_FIELD_NAME")
    milvus_text_field_name = os.getenv("TEXT_FIELD_NAME")
    milvus_metadata_field_name = os.getenv("METADATA_FIELD_NAME")
    milvus_id_field_name = os.getenv("ID_FIELD_NAME")


    # --------------------------------------------------------
    # Source documentation to create vector embeddings for.
    # --------------------------------------------------------
    source = MongoDocumentSource(
        mongo_uri=f"mongodb://{mongo_host}:27017",
        database=mongo_db,
        collection=mongo_collection
    )

    # --------------------------------------------------------
    # Embedding model
    # --------------------------------------------------------
    embedding_model = ONNXEmbeddingModel(
        download_model=download_model,
        model_name=model_name,
        model_path=model_path,
        batch_size=32
    )

    # --------------------------------------------------------
    # Vector database
    # --------------------------------------------------------
    vector_store = MilvusVectorStore(
        uri=f'http://{milvus_host}:19530',
        collection_name=milvus_collection,
        embedding_field_name=milvus_embedding_field_name,
        text_field_name=milvus_text_field_name,
        metadata_field_name=milvus_metadata_field_name,
        id_field_name=milvus_id_field_name,
    )

    # --------------------------------------------------------
    # Pipeline
    # --------------------------------------------------------
    pipeline = IngestionPipeline(
        source=source,
        embedding_model=embedding_model,
        vector_store=vector_store,
        batch_size=32
    )

    pipeline.run()


if __name__ == "__main__":
    main()