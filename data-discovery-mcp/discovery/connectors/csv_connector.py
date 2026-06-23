from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Sequence

from discovery.connectors.base import BaseConnector, ColumnSchema, DataObjectSchema


class CSVConnector(BaseConnector):
    """Read schemas and sample rows from CSV files in one directory."""

    def __init__(self, source_id: str, directory_path: Path, sample_size: int = 5, sniff_size: int = 50) -> None:
        super().__init__(source_id=source_id, sample_size=sample_size)
        self.directory_path = Path(directory_path)
        self.sniff_size = sniff_size

    def list_objects(self) -> List[str]:
        return sorted(path.name for path in self.directory_path.glob("*.csv") if path.is_file())

    def get_schema(self, path: str) -> DataObjectSchema:
        csv_name = self._normalize_csv_name(path)
        csv_path = self.directory_path / csv_name
        if not csv_path.exists() or not csv_path.is_file():
            raise ValueError(f"CSV file '{path}' was not found in source '{self.source_id}'")

        with csv_path.open(newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            fieldnames = list(reader.fieldnames or [])
            rows = [row for _, row in zip(range(self.sniff_size), reader)]

        sample_rows = rows[: self.sample_size]
        columns = [
            ColumnSchema(
                name=column_name,
                data_type=self._infer_type([row.get(column_name, "") for row in rows]),
                nullable=any(row.get(column_name, "") == "" for row in rows),
            )
            for column_name in fieldnames
        ]

        return DataObjectSchema(
            source_id=self.source_id,
            object_type="file",
            path=csv_name,
            title=csv_name,
            columns=columns,
            sample_rows=sample_rows,
            metadata={
                "file_path": str(csv_path),
                "format": "csv",
                "sampled_rows": len(rows),
            },
        )

    @staticmethod
    def _normalize_csv_name(path: str) -> str:
        stripped = path.strip()
        return stripped if stripped.endswith(".csv") else f"{stripped}.csv"

    @classmethod
    def _infer_type(cls, values: Sequence[str]) -> str:
        non_empty_values = [value.strip() for value in values if value is not None and value.strip() != ""]
        if not non_empty_values:
            return "text"

        checks = [
            ("integer", cls._is_integer),
            ("float", cls._is_float),
            ("boolean", cls._is_boolean),
            ("date", cls._is_date),
            ("datetime", cls._is_datetime),
        ]
        for type_name, predicate in checks:
            if all(predicate(value) for value in non_empty_values):
                return type_name
        return "text"

    @staticmethod
    def _is_integer(value: str) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_float(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_boolean(value: str) -> bool:
        return value.lower() in {"true", "false", "yes", "no", "0", "1"}

    @staticmethod
    def _is_date(value: str) -> bool:
        try:
            date.fromisoformat(value)
            return "T" not in value and " " not in value
        except ValueError:
            return False

    @staticmethod
    def _is_datetime(value: str) -> bool:
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

