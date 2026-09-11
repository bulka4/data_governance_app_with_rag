from typing import Iterator
from pymongo import MongoClient

from .DocumentSource import DocumentSource
from .data_models import MongoTableDocument, MongoColumnDocument
from data_models import DocumentChunk

class MongoDocumentSource(DocumentSource):
    '''
    - Implementation of the DocumentSource interface representing a source documentation stored in the MongoDB database.
    - Used to prepare text chunks from which we can create vector embeddings.
    - We assume here that the documentation in MongoDB is about tables and columns and has following schema:
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
    '''
    def __init__(
        self,
        mongo_uri: str,
        database: str,
        collection: str
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database]
        self.collection = self.db[collection]

    def read_chunks(self) -> Iterator[DocumentChunk]:
        '''
        Create chunks with table and column descriptions for all documents in the MongoDB collection specified by the 
        'client', 'db' and 'collection' attributes of this class.
        '''
        for raw_document in self.collection.find():
            # print(raw_document)

            # Convert the document into the MongoTableDocument object
            document: MongoTableDocument = MongoTableDocument.from_mongo(raw_document)

            # print(raw_document.get('tableName'))
            # print(raw_document.get('tableDescription'))
            
            yield from self._document_to_chunks(document)



    def _document_to_chunks(
        self,
        document: MongoTableDocument,
        chunk_size: int = 20,
        overlap: int = 5
    ) -> Iterator[DocumentChunk]:
        '''
        Create chunks with table and column descriptions for a single MongoTableDocument object representing a MongoDB document.

        Arguments:
            - document - this argument is prepared using the MongoTableDocument.from_mongo() function which converts a raw Mongo document
                into the MongoTableDocument object.
        '''

        chunk_id = 0

        # ----------------------------------------------------
        # Prepare chunks for the table documentation
        # ----------------------------------------------------
        if document.table_description:
            table_text = self._build_table_text(document)

            for text_chunk in self._split_text(
                table_text,
                chunk_size,
                overlap
            ):
                yield DocumentChunk(
                    text=text_chunk,
                    object_type="table",
                    object_name=document.table_name,
                    object_id=document.table_id,
                    chunk_id=chunk_id
                )

                chunk_id += 1


        # ----------------------------------------------------
        # Prepare chunks for the column documentation
        # ----------------------------------------------------
        for column in document.columns:
            column_text = self._build_column_text(
                document,
                column
            )

            if not column_text:
                continue

            for text_chunk in self._split_text(
                column_text,
                chunk_size,
                overlap
            ):
                yield DocumentChunk(
                    text=text_chunk,
                    object_type="column",
                    object_name=column.column_name,
                    object_id=column.column_id,
                    chunk_id=chunk_id
                )

                chunk_id += 1



    def _split_text(
        self,
        text: str,
        chunk_size: int,
        overlap: int
    ) -> Iterator[str]:
        'Prepare chunks for a given text using a specific chunk size (length in words) and overlap (number of words each chunk overlaps).'
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        if overlap < 0:
            raise ValueError("overlap must not be negative")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        step = chunk_size - overlap
        words = text.split()

        for start in range(0, len(text), step):
            chunk_words = words[start:start + chunk_size]

            if not chunk_words:
                break

            yield " ".join(chunk_words)

            if start + chunk_size >= len(words):
                break



    @staticmethod
    def _build_table_text(
        document: MongoTableDocument
    ) -> str:
        "The document argument is prepared using the MongoTableDocument.from_mongo() function which converts a raw Mongo document"
        "into the MongoTableDocument object."

        text_parts = [f"Table: {document.table_name}"]

        if document.table_description:
            text_parts.append(f"Description: {document.table_description}")

        if document.source_script:
            text_parts.append(f"Source SQL: {document.source_script}")

        return "\n".join(text_parts)



    @staticmethod
    def _build_column_text(
        table: MongoTableDocument,
        column: MongoColumnDocument
    ) -> str:
        "The document argument is prepared using the MongoTableDocument.from_mongo() function which converts a raw Mongo document"
        "into the MongoTableDocument object."

        text_parts = [
            f"Table: {table.table_name}",
            f"Column: {column.column_name}"
        ]

        if column.column_description:
            text_parts.append(f"Description: {column.column_description}")

        return "\n".join(text_parts)