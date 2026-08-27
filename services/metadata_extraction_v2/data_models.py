from dataclasses import dataclass, field
from typing import Literal


class Column:
    """
    Represents a column belonging to a SQL table.

    Foreign-key, primary-key and description information is intentionally
    not extracted from SQL Server. These fields can be populated later
    by the application.
    """

    column_name: str
    foreign_key: bool = False
    primary_key: bool = False
    column_description: str | None = None
    column_description_encoded: list | None = None


class Table:
    """
    Represents a table that will eventually be stored in the
    MongoDB `tablesDocs` collection.
    """

    table_id: int
    table_name: str
    source_script: str | None = None
    table_description: str | None = None
    table_description_encoded: list | None = None
    columns: list[Column] = field(default_factory=list)


class Script:
    """
    Represents a SQL Server code object.

    A script can currently be a stored procedure or a view.
    `input_tables` contains tables/views used by the script.
    `output_table` is the table/view produced by the script.
    """

    script_name: str
    script_type: str
    content: str
    input_tables: list[str] = field(default_factory=list)
    output_table: str | None = None