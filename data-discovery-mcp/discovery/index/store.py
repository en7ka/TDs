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
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def replace_source(self, source_id: str, documents: List[Dict[str, Any]]) -> int:
        with self.connection as connection:
            existing_rows = connection.execute(
                "SELECT id FROM documents WHERE source_id = ?",
                (source_id,),
            ).fetchall()
            connection.executemany(
                "DELETE FROM documents_fts WHERE rowid = ?",
                [(row["id"],) for row in existing_rows],
            )
            connection.execute("DELETE FROM documents WHERE source_id = ?", (source_id,))
            for document in documents:
                cursor = connection.execute(
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
                    (
                        document["source_id"],
                        document["object_type"],
                        document["path"],
                        document["title"],
                        document["text"],
                        json.dumps(document.get("metadata", {}), ensure_ascii=False, sort_keys=True),
                        json.dumps(document, ensure_ascii=False, sort_keys=True),
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO documents_fts(rowid, title, path, text)
                    VALUES (?, ?, ?, ?)
                    """,
                    (cursor.lastrowid, document["title"], document["path"], document["text"]),
                )
        return len(documents)

    def search_documents(self, match_query: str, limit: int = 20) -> List[Dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT
                d.document_json,
                bm25(documents_fts, 5.0, 3.0, 1.0) AS rank
            FROM documents_fts
            JOIN documents AS d ON d.id = documents_fts.rowid
            WHERE documents_fts MATCH ?
            ORDER BY rank, d.source_id, d.object_type, d.path
            LIMIT ?
            """,
            (match_query, limit),
        ).fetchall()

        results = []
        for row in rows:
            document = json.loads(row["document_json"])
            document["score"] = round(-float(row["rank"]), 6)
            results.append(document)
        return results

    def list_documents(self) -> List[Dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT document_json
            FROM documents
            ORDER BY source_id, object_type, path, title
            """
        ).fetchall()
        return [json.loads(row["document_json"]) for row in rows]

    def list_source_ids(self) -> List[str]:
        rows = self.connection.execute("SELECT DISTINCT source_id FROM documents ORDER BY source_id").fetchall()
        return [row["source_id"] for row in rows]

    def count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self.connection.close()

    def _initialize(self) -> None:
        with self.connection as connection:
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
            connection.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
                USING fts5(title, path, text)
                """
            )
