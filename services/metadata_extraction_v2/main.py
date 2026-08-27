"""
Main metadata extraction script.

This script:
1. Connects to SQL Server.
2. Extracts tables and columns using MSSQLExtractor.
3. Extracts SQL Server scripts and their dependencies.
4. Creates documents for `tablesDocs`.
5. Creates documents for `dataLineageDocs`.
6. Replaces the corresponding MongoDB collections.

The actual MongoDB schemas do not need to be recreated in Python.
The dictionaries produced here match the fields expected by the
Mongoose schemas.
"""

from SQLConnector import SQLConnector
from extract_metadata.MSSQLExtractor import MSSQLExtractor
from data_lineage import (
    create_data_lineage_docs,
    find_final_tables
)
from insert_metadata.InsertMetadataMongo import InsertMetadataMongo


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

# DNS name of the SQL Server
SQL_SERVER_DNS = "my_sql"
SQL_DATABASE = "master"

MONGO_URI = "mongodb://127.0.0.1:27017"
MONGO_DATABASE = "db_doc"


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    # Create the SQL Server connector using the existing SQLConnector
    # implementation.
    sql = SQLConnector(
        server=SQL_SERVER_DNS,
        database=SQL_DATABASE
    )

    # The MSSQL-specific implementation is hidden behind the
    # MetadataExtractor interface.
    extractor = MSSQLExtractor(sql)

    # Extract both kinds of metadata.
    tables, scripts = extractor.extract()

    print(f"Extracted {len(tables)} tables.")
    print(f"Extracted {len(scripts)} scripts.")

    # -------------------------------------------------------------
    # Prepare dataLineageDocs documents
    # -------------------------------------------------------------

    final_tables = find_final_tables(scripts)

    print(f"Found {len(final_tables)} final tables.")

    data_lineage_documents = []

    # MongoDB IDs are generated here in the same simple sequential
    # manner as in the old JavaScript implementation.
    for data_lineage_id, final_table in enumerate(
        final_tables,
        start=1
    ):
        document = create_data_lineage_docs(
            final_table=final_table,
            data_lineage_name=final_table,
            scripts=scripts,
            data_lineage_id=data_lineage_id
        )

        data_lineage_documents.append(document)

    # -------------------------------------------------------------
    # Insert medatadata into MongoDB to be used by the data governance backend
    # -------------------------------------------------------------

    metadata_insert = InsertMetadataMongo(
        mongo_uri=MONGO_URI,
        database_name=MONGO_DATABASE,
    )

    metadata_insert.insert_tables(tables)

    metadata_insert.insert_data_lineage(
        data_lineage_documents
    )

    print("Metadata extraction completed.")


if __name__ == "__main__":
    main()