from dataclasses import dataclass
from typing import Any

@dataclass
class MongoColumnDocument:
    "Representing a column from the 'columns' field in a document from the collection about tables."
    column_id: Any
    column_name: str
    column_description: str | None


@dataclass
class MongoTableDocument:
    "Representing a document from the collection about tables."
    table_id: int
    table_name: str
    source_script: str | None
    table_description: str | None
    table_description_encoded: list[float] | None
    columns: list[MongoColumnDocument]

    @classmethod
    def from_mongo(
        cls,
        document: dict[str, Any],
    ) -> "MongoTableDocument":
        '''
        Convert a MongoDB document into the MongoTableDocument object. That document should have the following schema:
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
        
        Arguments:
            - document - A MongoDB document obtained using PyMongo, e.g. using functions collection.find(), collection.find_one(), etc.
        '''
        columns = [
            MongoColumnDocument(
                column_id=(
                    column.get("id")
                    or f"{document['tableId']}:{column['columnName']}"
                ),
                column_name=column["columnName"],
                column_description=(
                    column.get("columnDescription")
                )
            )
            for column in document.get("columns", [])
        ]

        return cls(
            table_id=document["tableId"],
            table_name=document["tableName"],
            source_script=document.get("sourceScript"),
            table_description=document.get("tableDescription"),
            table_description_encoded=document.get("tableDescriptionEncoded"),
            columns=columns
        )