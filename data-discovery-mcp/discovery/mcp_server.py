from __future__ import annotations

from typing import Any, Dict, List

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:
    raise SystemExit(
        "The official MCP Python SDK is not installed. "
        "Use Python 3.10+ and install dependencies: "
        'python -m pip install -e ".[dev]"'
    ) from exc

from discovery.config import DEFAULT_INDEX_DB_PATH, create_connector, list_sources
from discovery.index.indexer import Indexer
from discovery.index.store import IndexStore
from discovery.search.service import SearchService


mcp = FastMCP("data-discovery-mcp")
store = IndexStore(DEFAULT_INDEX_DB_PATH)


@mcp.tool()
def listSources() -> List[Dict[str, str]]:
    """Return configured data sources."""
    return list_sources()


@mcp.tool()
def indexSource(sourceId: str) -> Dict[str, Any]:
    """Index one configured data source by source ID."""
    connector = create_connector(sourceId)
    indexed_count = Indexer(store).index_source(connector)
    return {"source_id": sourceId, "indexed_documents": indexed_count}


@mcp.tool()
def search(query: str) -> List[Dict[str, Any]]:
    """Search indexed tables, files, and columns by keyword."""
    return SearchService(store).search(query)


@mcp.tool()
def getSchema(sourceId: str, path: str) -> Dict[str, Any]:
    """Return schema and sample rows for a table or CSV file."""
    connector = create_connector(sourceId)
    return connector.get_schema(path).to_dict()


if __name__ == "__main__":
    mcp.run()
