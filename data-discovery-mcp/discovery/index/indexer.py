from __future__ import annotations

import json
from typing import Any, Dict, List

from discovery.connectors.base import BaseConnector, DataObjectSchema
from discovery.index.store import IndexStore


class Indexer:
    """Build normalized keyword documents from connector metadata."""

    def __init__(self, store: IndexStore) -> None:
        self.store = store

    def index_source(self, connector: BaseConnector) -> int:
        documents: List[Dict[str, Any]] = []
        for schema in connector.iter_schemas():
            documents.extend(self._documents_for_schema(schema))
        return self.store.replace_source(connector.source_id, documents)

    def _documents_for_schema(self, schema: DataObjectSchema) -> List[Dict[str, Any]]:
        object_document = {
            "source_id": schema.source_id,
            "object_type": schema.object_type,
            "path": schema.path,
            "title": schema.title,
            "text": self._object_text(schema),
            "metadata": {
                **schema.metadata,
                "columns": [column.to_dict() for column in schema.columns],
                "sample_rows": schema.sample_rows,
            },
        }
        column_documents = [
            {
                "source_id": schema.source_id,
                "object_type": "column",
                "path": f"{schema.path}.{column.name}",
                "title": f"{schema.title}.{column.name}",
                "text": self._column_text(schema, column.to_dict()),
                "metadata": {
                    "parent_path": schema.path,
                    "parent_type": schema.object_type,
                    "column": column.to_dict(),
                    "sample_values": self._sample_values(schema, column.name),
                },
            }
            for column in schema.columns
        ]
        return [object_document] + column_documents

    @staticmethod
    def _object_text(schema: DataObjectSchema) -> str:
        column_text = " ".join(f"{column.name} {column.data_type}" for column in schema.columns)
        sample_text = json.dumps(schema.sample_rows[:3], ensure_ascii=False, sort_keys=True)
        metadata_text = json.dumps(schema.metadata, ensure_ascii=False, sort_keys=True)
        return f"{schema.object_type} {schema.title} {schema.path} columns {column_text} metadata {metadata_text} samples {sample_text}"

    @staticmethod
    def _column_text(schema: DataObjectSchema, column: Dict[str, Any]) -> str:
        sample_values = Indexer._sample_values(schema, column["name"])
        return (
            f"column {column['name']} type {column['type']} "
            f"source {schema.source_id} parent {schema.title} {schema.path} "
            f"samples {json.dumps(sample_values, ensure_ascii=False, sort_keys=True)}"
        )

    @staticmethod
    def _sample_values(schema: DataObjectSchema, column_name: str) -> List[Any]:
        values = []
        for row in schema.sample_rows:
            if column_name in row and row[column_name] not in values:
                values.append(row[column_name])
        return values[:5]

