from abc import ABC, abstractmethod
from ..dataclasses import Table


class InsertMetadata(ABC):
    """
    Interface for inserting metadata into a database that will be used by the data governance backend.

    Implementations can store metadata in MongoDB, PostgreSQL,
    another database, an API, etc.
    """

    @abstractmethod
    def insert_tables(self, tables: list[Table]):
        """
        Insert table metadata.
        """
        pass

    @abstractmethod
    def insert_data_lineage(self, data_lineage_docs: list[dict]):
        """
        Insert data lineage metadata.
        """
        pass