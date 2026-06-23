from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from discovery.connectors.base import BaseConnector
from discovery.connectors.csv_connector import CSVConnector
from discovery.connectors.sqlite_connector import SQLiteConnector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
DEFAULT_INDEX_DB_PATH = PROJECT_ROOT / ".data_discovery_index.sqlite"


@dataclass(frozen=True)
class SourceConfig:
    source_id: str
    kind: str
    path: Path

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "path": str(self.path),
        }


def get_default_sources() -> Dict[str, SourceConfig]:
    sources = [
        SourceConfig(
            source_id="sqlite_demo",
            kind="sqlite",
            path=SAMPLE_DATA_DIR / "demo.db",
        ),
        SourceConfig(
            source_id="csv_demo",
            kind="csv",
            path=SAMPLE_DATA_DIR,
        ),
    ]
    return {source.source_id: source for source in sources}


def list_sources() -> List[Dict[str, str]]:
    return [source.to_dict() for source in get_default_sources().values()]


def get_source_config(source_id: str) -> SourceConfig:
    sources = get_default_sources()
    if source_id not in sources:
        known_sources = ", ".join(sorted(sources))
        raise ValueError(f"Unknown source '{source_id}'. Known sources: {known_sources}")
    return sources[source_id]


def create_connector(source_id: str) -> BaseConnector:
    source = get_source_config(source_id)
    if source.kind == "sqlite":
        return SQLiteConnector(source_id=source.source_id, database_path=source.path)
    if source.kind == "csv":
        return CSVConnector(source_id=source.source_id, directory_path=source.path)
    raise ValueError(f"Unsupported source kind '{source.kind}' for source '{source.source_id}'")

