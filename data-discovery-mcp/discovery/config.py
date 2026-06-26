from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from discovery.connectors.base import BaseConnector
from discovery.connectors.csv_connector import CSVConnector
from discovery.connectors.sqlite_connector import SQLiteConnector


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_DB_PATH = PROJECT_ROOT / ".data_discovery_index.sqlite"
DEFAULT_SOURCES_CONFIG_PATH = PROJECT_ROOT / "sources.json"


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
    config_path = Path(os.environ.get("DATA_DISCOVERY_SOURCES_CONFIG", DEFAULT_SOURCES_CONFIG_PATH))
    sources = load_sources(config_path)
    return {source.source_id: source for source in sources}


def load_sources(config_path: Path) -> List[SourceConfig]:
    path = config_path if config_path.is_absolute() else PROJECT_ROOT / config_path
    with path.open(encoding="utf-8") as file_obj:
        payload = json.load(file_obj)

    raw_sources = payload["sources"] if isinstance(payload, dict) else payload
    return [_source_from_dict(path.parent, item) for item in raw_sources]


def _source_from_dict(config_dir: Path, item: Dict[str, Any]) -> SourceConfig:
    raw_path = Path(item["path"])
    source_path = raw_path if raw_path.is_absolute() else config_dir / raw_path
    return SourceConfig(
        source_id=item["source_id"],
        kind=item["kind"],
        path=source_path,
    )


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
