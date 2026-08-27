from dataclasses import Script


def create_data_lineage_docs(
    final_table: str,
    data_lineage_name: str,
    scripts: list[Script],
    data_lineage_id: int,
) -> dict:
    """
    Create one document for the `dataLineageDocs` MongoDB collection.

    The function corresponds to the old JavaScript
    `createDataLineageDocs()` + `createNodes()` logic.

    It does not insert anything into MongoDB. It only prepares the
    document so that the caller can decide how and when to persist it.
    """

    data_lineage_doc = {
        "dataLineageId": data_lineage_id,
        "dataLineageName": data_lineage_name,
        "nodes": [],
    }

    _create_nodes(
        data_lineage_doc=data_lineage_doc,
        scripts=scripts,
        table=final_table,
        first_iteration=True,
        visited_tables=set(),
        visited_scripts=set(),
    )

    return data_lineage_doc


def _create_nodes(
    data_lineage_doc: dict,
    scripts: list[Script],
    table: str,
    first_iteration: bool,
    visited_tables: set[str],
    visited_scripts: set[str],
) -> None:
    """
    Recursively create table/script nodes.

    `visited_tables` and `visited_scripts` prevent infinite recursion
    when SQL objects contain cyclic dependencies.
    """

    if table in visited_tables:
        return

    visited_tables.add(table)

    # The first node is the final table itself.
    if first_iteration:
        data_lineage_doc["nodes"].append(
            {
                "value": table,
                "type": "table",
                "linkedTo": [],
            }
        )

    # Find the script which creates this table.
    producer = _find_producer(
        scripts=scripts,
        output_table=table,
    )

    if producer is None:
        return

    # Avoid processing the same script twice.
    if producer.script_name in visited_scripts:
        return

    visited_scripts.add(producer.script_name)

    # Add the script node.
    data_lineage_doc["nodes"].append(
        {
            "value": producer.script_name,
            "type": "script",
            "script": producer.content,
            "linkedTo": [table],
        }
    )

    # Add all source table nodes.
    for input_table in producer.input_tables:
        data_lineage_doc["nodes"].append(
            {
                "value": input_table,
                "type": "table",
                "linkedTo": [producer.script_name],
            }
        )

    # Recursively find what creates every source table.
    for input_table in producer.input_tables:
        _create_nodes(
            data_lineage_doc=data_lineage_doc,
            scripts=scripts,
            table=input_table,
            first_iteration=False,
            visited_tables=visited_tables,
            visited_scripts=visited_scripts,
        )


def _find_producer(
    scripts: list[Script],
    output_table: str,
) -> Script | None:
    """
    Find the script responsible for creating a particular table/view.

    This preserves the behavior of the old JavaScript implementation,
    which used the first matching script.
    """

    for script in scripts:
        if script.output_table == output_table:
            return script

    return None


def find_final_tables(
    scripts: list[Script],
) -> list[str]:
    """
    Find tables/views which are outputs of scripts but are never inputs
    to another script.

    Such objects are considered final tables for the purpose of creating
    data lineage documents.
    """

    output_tables = {
        script.output_table
        for script in scripts
        if script.output_table is not None
    }

    input_tables = {
        input_table
        for script in scripts
        for input_table in script.input_tables
    }

    final_tables = output_tables - input_tables

    return sorted(final_tables)