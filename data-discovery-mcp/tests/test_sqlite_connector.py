from pathlib import Path

from discovery.connectors.sqlite_connector import SQLiteConnector


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_sqlite_connector_reads_tables_schema_and_samples() -> None:
    connector = SQLiteConnector("sqlite_demo", PROJECT_ROOT / "sample_data" / "demo.db")

    assert connector.list_objects() == ["orders", "products", "users"]

    schema = connector.get_schema("users")
    column_types = {column.name: column.data_type.upper() for column in schema.columns}

    assert schema.source_id == "sqlite_demo"
    assert schema.object_type == "table"
    assert schema.path == "users"
    assert column_types["email"] == "TEXT"
    assert schema.sample_rows[0]["email"] == "alice@example.com"
    assert schema.metadata["row_count"] == 4

