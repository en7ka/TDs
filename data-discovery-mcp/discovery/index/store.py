from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class IndexStore:
    """Small SQLite-backed document store for discovery metadata."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def replace_source(self, source_id: str, documents: List[Dict[str, Any]]) -> int:
        with self._connect() as connection:
            connection.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            connection.executemany(
                """
                INSERT INTO documents (
                    source_id,
                    object_type,
                    path,
                    title,
                    text,
                    metadata_json,
                    document_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        document["source_id"],
                        document["object_type"],
                        document["path"],
                        document["title"],
                        document["text"],
                        json.dumps(document.get("metadata", {}), ensure_ascii=False, sort_keys=True),
                        json.dumps(document, ensure_ascii=False, sort_keys=True),
                    )
                    for document in documents
                ],
            )
        return len(documents)

    def list_documents(self) -> List[Dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT document_json
                FROM documents
                ORDER BY source_id, object_type, path, title
                """
            ).fetchall()
        return [json.loads(row["document_json"]) for row in rows]

    def list_source_ids(self) -> List[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT DISTINCT source_id FROM documents ORDER BY source_id").fetchall()
        return [row["source_id"] for row in rows]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        return int(row["count"])

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    object_type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    document_json TEXT NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id)")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

