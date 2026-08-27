# Introduction
The main.py script:
- Reads a documentation from the MongoDB database (all documents from a specific database and collection)
- Converts it into embeddings
    - It uses for that a saved ONNX model or downloads a new model from Hugging Face if such a model is not saved yet
- Clears a Milvus collection and inserts new embeddings

# MongoDocumentSource
The `document_source/MongoDocumentSource.py` script contains the `MongoDocumentSource` class used to prepare text chunks from which we can create vector embeddings.

We assume there that the documentation in MongoDB is about tables and columns and has following schema:
```
    col_doc_schema:
        {
            columnName: String
            ,foreignKey: Boolean
            ,primaryKey: Boolean
            ,columnDescription: String
            ,columnDescriptionEncoded: Array
        }

    table_doc_schema:
        {
            tableId: Number
            ,tableName: String
            ,sourceScript: String
            ,tableDescription: String
            ,tableDescriptionEncoded: Array
            ,columns: [col_doc_schema]
        }
```

# ONNXEmbeddingModel
Using the `ONNXEmbeddingModel` class from the `embedding_model/ONNXEmbeddingModel.py` script we can download a new model from Hugging Face and save it in the ONNX format or load already saved ONNX model and load this model to be ready to use.

# MilvusVectorStore
Using the `MilvusVectorStore` class from the `vector_store/MilvusVectorStore.py` script we can insert vector embeddings into a collection with the following fields:
- id: INT64
- embedding: FLOAT_VECTOR
- text: VARCHAR
- metadata: JSON

Before inserting embeddings, all the current embeddings in the collection are removed.

Embeddings are generated using the `ONNXEmbeddingModel` class.