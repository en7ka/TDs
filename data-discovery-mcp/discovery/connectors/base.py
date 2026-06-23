from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class ColumnSchema:
    """Normalized description of a column from any supported source."""

    name: str
    data_type: str
    nullable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.data_type,
            "nullable": self.nullable,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class DataObjectSchema:
    """Normalized schema and metadata for a table or a file."""

    source_id: str
    object_type: str
    path: str
    title: str
    columns: List[ColumnSchema]
    sample_rows: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "object_type": self.object_type,
            "path": self.path,
            "title": self.title,
            "columns": [column.to_dict() for column in self.columns],
            "sample_rows": self.sample_rows,
            "metadata": self.metadata,
        }


class BaseConnector(ABC):
    """Common interface for all metadata connectors."""

    def __init__(self, source_id: str, sample_size: int = 5) -> None:
        self.source_id = source_id
        self.sample_size = sample_size

    @abstractmethod
    def list_objects(self) -> List[str]:
        """Return table names, file names, or other discoverable paths."""

    @abstractmethod
    def get_schema(self, path: str) -> DataObjectSchema:
        """Return normalized schema and sample rows for one object."""

    def iter_schemas(self) -> Iterable[DataObjectSchema]:
        for path in self.list_objects():
            yield self.get_schema(path)

