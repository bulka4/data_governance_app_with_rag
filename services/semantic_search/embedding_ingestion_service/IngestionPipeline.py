from data_models import DocumentChunk

from document_source.MongoDocumentSource import MongoDocumentSource
from document_source.DocumentSource import DocumentSource

from embedding_model.ONNXEmbeddingModel import ONNXEmbeddingModel
from embedding_model.EmbeddingModel import EmbeddingModel

from vector_store.MilvusVectorStore import MilvusVectorStore
from vector_store.VectorStore import VectorStore

from typing import Iterator

class IngestionPipeline:
    '''
    Class for running a pipeline wich:
        - selects text chunks from an entire source documentation
        - generates embeddings for the selected text chunks
        - cleares a collection in a vector store and inserts new embeddings into it.
    '''
    def __init__(
        self,
        mongo_host,
        mongo_db,
        mongo_collection,
        download_model,
        model_name,
        model_path,
        milvus_host,
        milvus_collection,
        milvus_embedding_field_name,
        milvus_text_field_name,
        milvus_metadata_field_name,
        milvus_id_field_name,
        batch_size: int = 64
    ):
        '''
        Arguments:
            - source - object representing the source documentation for which to create embeddings
            - embedding_model - object representing the model used to generate embeddings
            - vector_store - object representing the vector store where insert embeddings to
            - batch_size - Batch size for the model - i.e. for how many texts to generate emebddings at once.
        '''
        self.source: DocumentSource = MongoDocumentSource(
            mongo_uri=f"mongodb://{mongo_host}:27017",
            database=mongo_db,
            collection=mongo_collection
        )
    
        self.embedding_model: EmbeddingModel = ONNXEmbeddingModel(
            download_model=download_model,
            model_name=model_name,
            model_path=model_path,
            batch_size=32
        )
    
        self.vector_store: VectorStore = MilvusVectorStore(
            uri=f"http://{milvus_host}:19530",
            collection_name=milvus_collection,
            embedding_field_name=milvus_embedding_field_name,
            text_field_name=milvus_text_field_name,
            metadata_field_name=milvus_metadata_field_name,
            id_field_name=milvus_id_field_name,
        )

        self.batch_size = batch_size



    def ingest(self) -> None:
        'Run the pipeline for generating and inserting embeddings into a vector store.'
        # Clear the existing collection.
        self.vector_store.clear()

        chunks_batch: list[DocumentChunk] = []
        # document_chunks contains chunks for all the documents from the source given by the self.source
        document_chunks: Iterator[DocumentChunk] = self.source.read_chunks()

        for chunk in document_chunks:
            print('Ingesting a text chunk: ', chunk.text)
            chunks_batch.append(chunk)

            if len(chunks_batch) >= self.batch_size:
                self._process_batch(chunks_batch)
                chunks_batch = []

        # Process final incomplete batch.
        if chunks_batch:
            self._process_batch(chunks_batch)



    def _process_batch(
        self,
        chunks: list[DocumentChunk]
    ) -> None:
        '''
        Generate embeddings and insert them into a storage for one batch of documents.
        '''
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_model.embed(texts)

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "The number of embeddings does not match the number of document chunks."
            )

        self.vector_store.insert(
            chunks,
            embeddings
        )

        print('Ingested text chunks')