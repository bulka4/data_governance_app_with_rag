from dataclasses import Table, Script

from abc import ABC, abstractmethod

class MetadataExtractor(ABC):
    """
    Interface for extracting metadata from different SQL servers (MySQL, MS SQL, etc.).

    Different database systems can provide their own implementation,
    for example MSSQLExtractor, PostgreSQLExtractor, etc.
    """

    @abstractmethod
    def extract_tables(self) -> list[Table]:
        """
        Extract tables and columns.

        Foreign keys, primary keys and descriptions are intentionally
        not extracted here.
        """
        pass

    @abstractmethod
    def extract_scripts(self) -> list[Script]:
        """
        Extract database scripts/code objects and their lineage information.
        """
        pass

    def extract(self) -> tuple[list[Table], list[Script]]:
        """
        Extract all metadata required by the application.
        """
        tables = self.extract_tables()
        scripts = self.extract_scripts()

        return tables, scripts