from pymongo import MongoClient
from pymongo.errors import CollectionInvalid

from models.metadata import Metadata
from persistence.insert_metadata import InsertMetadata


class InsertMetadataMongo(InsertMetadata):
    """
    MongoDB implementation of InsertMetadata.

    This class owns all MongoDB-specific concerns:
    - connecting to MongoDB
    - creating collections
    - defining MongoDB validation schemas
    - converting Python dataclasses into MongoDB documents
    - inserting metadata
    """

    TABLES_COLLECTION = "tablesDocs"
    DATA_LINEAGE_COLLECTION = "dataLineageDocs"

    def __init__(
        self,
        mongo_uri: str,
        database_name: str,
    ):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]

    def create_collections(self) -> None:
        """
        Create MongoDB collections with JSON Schema validators defined by the _tables_docs_schema 
        and _data_lineage_docs_schema functions.

        If the collections already exist, their validators are updated.
        """

        self._create_or_update_collection(
            collection_name=self.TABLES_COLLECTION,
            validator=self._tables_docs_schema(),
        )

        self._create_or_update_collection(
            collection_name=self.DATA_LINEAGE_COLLECTION,
            validator=self._data_lineage_docs_schema(),
        )

    def insert(self, metadata: Metadata) -> None:
        """
        Insert the complete Metadata object into MongoDB.

        Existing metadata is removed first, matching the behavior of the old JavaScript scripts.

        Create collections if they don't exist yet. Their schema is defined by the _tables_docs_schema 
        and _data_lineage_docs_schema functions.
        """

        # Make sure the collections exist before inserting.
        self.create_collections()

        # Convert dataclasses into MongoDB documents.
        table_documents = [
            self._table_to_document(table)
            for table in metadata.tables
        ]

        data_lineage_documents = [
            self._lineage_to_document(document)
            for document in metadata.data_lineage
        ]

        # Rebuild the collections.
        self.db[self.TABLES_COLLECTION].delete_many({})
        self.db[self.DATA_LINEAGE_COLLECTION].delete_many({})

        if table_documents:
            self.db[self.TABLES_COLLECTION].insert_many(
                table_documents
            )

        if data_lineage_documents:
            self.db[self.DATA_LINEAGE_COLLECTION].insert_many(
                data_lineage_documents
            )

    # -----------------------------------------------------------------
    # Collection management
    # -----------------------------------------------------------------

    def _create_or_update_collection(
        self,
        collection_name: str,
        validator: dict,
    ) -> None:
        """
        Create a collection if it doesn't exist.

        If it already exists, update its validator.

        MongoDB's `collMod` command is used to update the validator
        of an existing collection.
        """

        if collection_name not in self.db.list_collection_names():

            try:
                self.db.create_collection(
                    collection_name,
                    validator=validator,
                    validationLevel="strict",
                    validationAction="error",
                )
            except CollectionInvalid:
                # Another process could have created the collection
                # between the existence check and create_collection().
                pass

        else:
            self.db.command(
                "collMod",
                collection_name,
                validator=validator,
                validationLevel="strict",
                validationAction="error",
            )

    # -----------------------------------------------------------------
    # MongoDB schemas
    # -----------------------------------------------------------------

    @staticmethod
    def _tables_docs_schema() -> dict:
        """
        MongoDB JSON Schema corresponding to the Mongoose:

            tablesDocs
                └── Table
                     └── Column
        """

        column_schema = {
            "bsonType": "object",

            "required": [
                "columnName",
            ],

            "properties": {
                "columnName": {
                    "bsonType": "string",
                },

                "foreignKey": {
                    "bsonType": "bool",
                },

                "primaryKey": {
                    "bsonType": "bool",
                },

                "columnDescription": {
                    "bsonType": "string",
                },

                "columnDescriptionEncoded": {
                    "bsonType": "array",
                },
            },
        }

        return {
            "$jsonSchema": {
                "bsonType": "object",

                "required": [
                    "tableId",
                    "tableName",
                ],

                "properties": {
                    "tableId": {
                        "bsonType": "int",
                    },

                    "tableName": {
                        "bsonType": "string",
                    },

                    "sourceScript": {
                        "bsonType": [
                            "string",
                            "null",
                        ],
                    },

                    "tableDescription": {
                        "bsonType": [
                            "string",
                            "null",
                        ],
                    },

                    "tableDescriptionEncoded": {
                        "bsonType": [
                            "array",
                            "null",
                        ],
                    },

                    "columns": {
                        "bsonType": "array",
                        "items": column_schema,
                    },
                },
            }
        }

    @staticmethod
    def _data_lineage_docs_schema() -> dict:
        """
        MongoDB JSON Schema corresponding to the Mongoose:

            dataLineageDocs
                └── DataLineage
                     └── Node
        """

        node_schema = {
            "bsonType": "object",

            "required": [
                "value",
                "type",
            ],

            "properties": {
                "value": {
                    "bsonType": "string",
                },

                "type": {
                    "bsonType": "string",
                },

                "linkedTo": {
                    "bsonType": "array",
                },

                "script": {
                    "bsonType": "string",
                },

                "x": {
                    "bsonType": [
                        "double",
                        "int",
                        "long",
                        "null",
                    ],
                },

                "y": {
                    "bsonType": [
                        "double",
                        "int",
                        "long",
                        "null",
                    ],
                },
            },
        }

        return {
            "$jsonSchema": {
                "bsonType": "object",

                "required": [
                    "dataLineageId",
                    "dataLineageName",
                    "nodes",
                ],

                "properties": {
                    "dataLineageId": {
                        "bsonType": "int",
                    },

                    "dataLineageName": {
                        "bsonType": "string",
                    },

                    "nodes": {
                        "bsonType": "array",
                        "items": node_schema,
                    },
                },
            }
        }

    # -----------------------------------------------------------------
    # Dataclass -> MongoDB conversion
    # -----------------------------------------------------------------

    @staticmethod
    def _table_to_document(table) -> dict:
        """
        Convert a Table dataclass into a MongoDB document.
        """

        return {
            "tableId": table.table_id,
            "tableName": table.table_name,
            "sourceScript": table.source_script,
            "tableDescription": table.table_description,
            "tableDescriptionEncoded": (
                table.table_description_encoded
            ),
            "columns": [
                {
                    "columnName": column.column_name,
                    "foreignKey": column.foreign_key,
                    "primaryKey": column.primary_key,
                    "columnDescription": column.column_description,
                    "columnDescriptionEncoded": (
                        column.column_description_encoded
                    ),
                }
                for column in table.columns
            ],
        }

    @staticmethod
    def _lineage_to_document(document: dict) -> dict:
        """
        Data lineage documents are already represented as dictionaries
        matching the MongoDB document structure.

        Keeping this method separate makes it possible to perform
        additional MongoDB-specific transformations later.
        """

        return document

    def close(self) -> None:
        """
        Close the MongoDB connection.
        """

        self.client.close()