from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from discovery.connectors.base import BaseConnector, ColumnSchema, DataObjectSchema


class SQLiteConnector(BaseConnector):
    """Read table schemas and sample rows from a SQLite database."""

    def __init__(self, source_id: str, database_path: Path, sample_size: int = 5) -> None:
        super().__init__(source_id=source_id, sample_size=sample_size)
        self.database_path = Path(database_path)

    def list_objects(self) -> List[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            ).fetchall()
        return [row["name"] for row in rows]

    def get_schema(self, path: str) -> DataObjectSchema:
        table_name = path.strip()
        quoted_table = self._quote_identifier(table_name)
        with self._connect() as connection:
            table_exists = connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                  AND name NOT LIKE 'sqlite_%'
                """,
                (table_name,),
            ).fetchone()
            if table_exists is None:
                raise ValueError(f"Table '{path}' was not found in source '{self.source_id}'")

            column_rows = connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()
            sample_rows = connection.execute(
                f"SELECT * FROM {quoted_table} LIMIT ?",
                (self.sample_size,),
            ).fetchall()
            row_count = self._count_rows(connection, quoted_table)

        columns = [
            ColumnSchema(
                name=row["name"],
                data_type=row["type"] or "UNKNOWN",
                nullable=not bool(row["notnull"]) and not bool(row["pk"]),
                metadata={
                    "default_value": row["dflt_value"],
                    "primary_key": bool(row["pk"]),
                },
            )
            for row in column_rows
        ]

        return DataObjectSchema(
            source_id=self.source_id,
            object_type="table",
            path=table_name,
            title=table_name,
            columns=columns,
            sample_rows=[dict(row) for row in sample_rows],
            metadata={
                "database_path": str(self.database_path),
                "row_count": row_count,
            },
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _count_rows(self, connection: sqlite3.Connection, quoted_table: str) -> int:
        row = connection.execute(f"SELECT COUNT(*) AS count FROM {quoted_table}").fetchone()
        return int(row["count"])

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'
