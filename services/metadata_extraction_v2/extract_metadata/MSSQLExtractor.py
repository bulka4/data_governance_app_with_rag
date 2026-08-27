'''
Implementation of the MetadataExtractor interface for extracting metadata from the MS SQL Server.
'''

import re
import pandas as pd

from dataclasses import Table, Column, Script
from MetadataExtractor import MetadataExtractor
from ..SQLConnector import SQLConnector


class MSSQLExtractor(MetadataExtractor):
    """
    Implementation of the MetadataExtractor interface for extracting metadata from the MS SQL Server.

    It scans all non-system databases on the server and extracts:
    - tables
    - columns
    - views
    - stored procedures

    It deliberately does NOT extract:
    - primary keys
    - foreign keys
    - column descriptions
    - table descriptions
    """

    SYSTEM_DATABASES = {
        "master",
        "tempdb",
        "model",
        "msdb",
        "Monitoring",
    }

    def __init__(
        self,
        sql_connector: SQLConnector,
    ):
        self.sql = sql_connector

    def extract_tables(self) -> list[Table]:
        """
        Extract all tables and their columns from all databases.

        The resulting Table objects are ready to be converted into
        MongoDB documents for the `tablesDocs` collection.
        """

        database_names = self._get_database_names()

        # Collect pairs of:
        #
        #     database.schema.table
        #     column
        #
        # before grouping them into Table objects.
        table_columns: list[tuple[str, str]] = []

        for database in database_names:
            database_identifier = self._quote_identifier(database)

            query = f"""
                SELECT
                    CONCAT(
                        table_catalog,
                        '.',
                        table_schema,
                        '.',
                        table_name
                    ) AS table_name,
                    column_name
                FROM {database_identifier}.INFORMATION_SCHEMA.COLUMNS
            """

            df = self.sql.read_query(query)

            for _, row in df.iterrows():
                table_name = str(row["table_name"]).lower()
                column_name = str(row["column_name"])

                table_columns.append(
                    (table_name, column_name)
                )

        # Sort in the same general way as the old JavaScript code.
        table_columns.sort(
            key=lambda x: (
                x[0].lower(),
                x[1].lower(),
            )
        )

        # Group columns belonging to the same table.
        tables: list[Table] = []

        current_table_name: str | None = None
        current_columns: list[Column] = []
        table_id = 0

        for table_name, column_name in table_columns:

            if current_table_name != table_name:

                # Save the previous table.
                if current_table_name is not None:
                    tables.append(
                        Table(
                            table_id=table_id,
                            table_name=current_table_name,
                            columns=current_columns,
                        )
                    )

                    table_id += 1

                current_table_name = table_name
                current_columns = []

            current_columns.append(
                Column(
                    column_name=column_name
                )
            )

        # Save the final table.
        if current_table_name is not None:
            tables.append(
                Table(
                    table_id=table_id,
                    table_name=current_table_name,
                    columns=current_columns,
                )
            )

        return tables

    def extract_scripts(self) -> list[Script]:
        """
        Extract views and stored procedures.

        For every script we determine:

        - script name
        - script type
        - original SQL code
        - input tables/views
        - output table/view

        The SQL parser here intentionally remains relatively simple,
        matching the approach of the old JavaScript implementation.
        """

        database_names = self._get_database_names()

        # We first need to know all tables and views because they are
        # used to determine whether identifiers occurring after FROM/JOIN
        # are actual database objects.
        tables = self._get_table_names(database_names)
        views = self._get_view_names(database_names)

        known_objects = tables | views

        scripts: list[Script] = []

        # -------------------------------------------------------------
        # Stored procedures
        # -------------------------------------------------------------

        for database in database_names:
            database_identifier = self._quote_identifier(database)

            query = f"""
                SELECT
                    SCHEMA_NAME(p.schema_id) AS schema_name,
                    p.name AS procedure_name,
                    m.definition AS definition
                FROM {database_identifier}.sys.procedures AS p
                LEFT JOIN {database_identifier}.sys.sql_modules AS m
                    ON m.object_id = p.object_id
            """

            df = self.sql.read_query(query)

            for _, row in df.iterrows():
                definition = row["definition"]

                if pd.isna(definition) or definition is None:
                    continue

                definition = str(definition)

                script_name = (
                    f"{database}."
                    f"{row['schema_name']}."
                    f"{row['procedure_name']}"
                ).lower()

                cleaned_definition = self._clean_sql(definition)

                # The old implementation only considered procedures
                # containing both INTO and FROM.
                if " into " not in f" {cleaned_definition} ":
                    continue

                if " from " not in f" {cleaned_definition} ":
                    continue

                output_table = self._extract_output_table(
                    cleaned_definition,
                    database,
                )

                if output_table is None:
                    continue

                # Do not create lineage if the output object is unknown.
                if output_table not in known_objects:
                    continue

                input_tables = self._extract_input_tables(
                    cleaned_definition,
                    database,
                    known_objects,
                )

                # A self-reference would create a cyclic lineage graph.
                if output_table in input_tables:
                    continue

                scripts.append(
                    Script(
                        script_name=script_name,
                        script_type="procedure",
                        content=definition,
                        input_tables=input_tables,
                        output_table=output_table,
                    )
                )

        # -------------------------------------------------------------
        # Views
        # -------------------------------------------------------------

        for database in database_names:
            database_identifier = self._quote_identifier(database)

            query = f"""
                SELECT
                    SCHEMA_NAME(v.schema_id) AS schema_name,
                    v.name AS view_name,
                    m.definition AS definition
                FROM {database_identifier}.sys.views AS v
                JOIN {database_identifier}.sys.sql_modules AS m
                    ON m.object_id = v.object_id
            """

            df = self.sql.read_query(query)

            for _, row in df.iterrows():
                definition = row["definition"]

                if pd.isna(definition) or definition is None:
                    continue

                definition = str(definition)

                script_name = (
                    f"{database}."
                    f"{row['schema_name']}."
                    f"{row['view_name']}"
                ).lower()

                output_table = script_name

                cleaned_definition = self._clean_sql(definition)

                input_tables = self._extract_input_tables(
                    cleaned_definition,
                    database,
                    known_objects,
                )

                # Views always represent the creation of the view itself.
                for _ in input_tables:
                    pass

                if not input_tables:
                    continue

                scripts.append(
                    Script(
                        script_name=script_name,
                        script_type="view",
                        content=definition,
                        input_tables=input_tables,
                        output_table=output_table,
                    )
                )

        return scripts

    # -----------------------------------------------------------------
    # Database metadata
    # -----------------------------------------------------------------

    def _get_database_names(self) -> list[str]:
        """
        Return all databases which should be scanned.
        """

        query = """
            SELECT name
            FROM sys.databases
        """

        df = self.sql.read_query(query)

        return [
            str(row["name"])
            for _, row in df.iterrows()
            if str(row["name"]) not in self.SYSTEM_DATABASES
        ]

    def _get_table_names(
        self,
        databases: list[str],
    ) -> set[str]:
        """
        Return fully-qualified table names in the form:

            database.schema.table
        """

        tables: set[str] = set()

        for database in databases:
            database_identifier = self._quote_identifier(database)

            query = f"""
                SELECT
                    SCHEMA_NAME(schema_id) AS schema_name,
                    name AS table_name
                FROM {database_identifier}.sys.tables
            """

            df = self.sql.read_query(query)

            for _, row in df.iterrows():
                table_name = (
                    f"{database}."
                    f"{row['schema_name']}."
                    f"{row['table_name']}"
                ).lower()

                tables.add(table_name)

        return tables

    def _get_view_names(
        self,
        databases: list[str],
    ) -> set[str]:
        """
        Return fully-qualified view names in the form:

            database.schema.view
        """

        views: set[str] = set()

        for database in databases:
            database_identifier = self._quote_identifier(database)

            query = f"""
                SELECT
                    SCHEMA_NAME(schema_id) AS schema_name,
                    name AS view_name
                FROM {database_identifier}.sys.views
            """

            df = self.sql.read_query(query)

            for _, row in df.iterrows():
                view_name = (
                    f"{database}."
                    f"{row['schema_name']}."
                    f"{row['view_name']}"
                ).lower()

                views.add(view_name)

        return views

    # -----------------------------------------------------------------
    # SQL parsing
    # -----------------------------------------------------------------

    @staticmethod
    def _clean_sql(sql: str) -> str:
        """
        Perform the same basic SQL normalization that the old
        JavaScript cleanCode() function performed.
        """

        return (
            sql.lower()
            .replace("\n", " ")
            .replace("\t", " ")
            .replace("\r", " ")
            .replace("[", "")
            .replace("]", "")
        )

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """
        Safely quote a SQL Server identifier.

        This is used for database names because they are inserted into
        SQL statements as identifiers rather than SQL values.
        """

        escaped = identifier.replace("]", "]]")
        return f"[{escaped}]"

    def _extract_output_table(
        self,
        sql: str,
        database: str,
    ) -> str | None:
        """
        Extract the object appearing after INTO.

        Example:

            INSERT INTO Stage.dbo.customer
            SELECT ...

        becomes:

            stage.dbo.customer
        """

        match = re.search(
            r"\binto\s+([a-zA-Z0-9_.]+)",
            sql,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        identifier = match.group(1).strip().lower()

        return self._normalize_object_name(
            identifier,
            database,
        )

    def _extract_input_tables(
        self,
        sql: str,
        database: str,
        known_objects: set[str],
    ) -> list[str]:
        """
        Extract objects appearing after FROM and JOIN.

        The parser deliberately checks the extracted names against the
        known SQL Server tables/views, preventing arbitrary SQL words
        from becoming lineage nodes.
        """

        input_tables: list[str] = []

        pattern = (
            r"\b(?:from|join)\s+"
            r"([a-zA-Z0-9_.]+)"
        )

        matches = re.finditer(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )

        for match in matches:
            identifier = match.group(1).strip().lower()

            normalized_name = self._normalize_object_name(
                identifier,
                database,
            )

            if (
                normalized_name in known_objects
                and normalized_name not in input_tables
            ):
                input_tables.append(normalized_name)

        return input_tables

    @staticmethod
    def _normalize_object_name(
        object_name: str,
        current_database: str,
    ) -> str:
        """
        Convert SQL object names into the canonical representation:

            database.schema.object

        Examples:

            customer
            -> current_database.dbo.customer

            dbo.customer
            -> current_database.dbo.customer

            stage.dbo.customer
            -> stage.dbo.customer
        """

        parts = object_name.lower().split(".")

        if len(parts) == 1:
            return f"{current_database}.dbo.{parts[0]}"

        if len(parts) == 2:
            return f"{current_database}.{parts[0]}.{parts[1]}"

        if len(parts) == 3:
            return ".".join(parts)

        return object_name.lower()