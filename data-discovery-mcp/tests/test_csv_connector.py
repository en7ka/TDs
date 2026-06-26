import pytest

from pathlib import Path

from discovery.connectors.csv_connector import CSVConnector


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_csv_connector_reads_schema_and_samples() -> None:
    connector = CSVConnector("csv_demo", PROJECT_ROOT / "sample_data")

    schema = connector.get_schema("users.csv")

    assert schema.source_id == "csv_demo"
    assert schema.object_type == "file"
    assert schema.path == "users.csv"
    assert [column.name for column in schema.columns] == [
        "id",
        "email",
        "first_name",
        "last_name",
        "created_at",
        "is_active",
    ]
    assert {column.name: column.data_type for column in schema.columns}["id"] == "integer"
    assert {column.name: column.data_type for column in schema.columns}["email"] == "text"
    assert schema.sample_rows[0]["email"] == "alice@example.com"


def test_csv_connector_treats_zero_one_as_integer() -> None:
    assert CSVConnector._infer_type(["0", "1"]) == "integer"


def test_csv_connector_raises_for_missing_file() -> None:
    connector = CSVConnector("csv_demo", PROJECT_ROOT / "sample_data")

    with pytest.raises(ValueError, match="was not found"):
        connector.get_schema("missing.csv")
