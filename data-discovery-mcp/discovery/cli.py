from __future__ import annotations

import argparse
import json
from typing import Any

from discovery.config import DEFAULT_INDEX_DB_PATH, create_connector, list_sources
from discovery.index.indexer import Indexer
from discovery.index.store import IndexStore
from discovery.search.service import SearchService


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Discovery MCP demo CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("sources", help="List configured data sources")

    index_parser = subparsers.add_parser("index", help="Index one configured source")
    index_parser.add_argument("source_id", help="Source ID, for example sqlite_demo or csv_demo")

    search_parser = subparsers.add_parser("search", help="Search indexed metadata")
    search_parser.add_argument("query", help="Keyword query")
    search_parser.add_argument("--limit", type=int, default=20, help="Maximum number of results")

    schema_parser = subparsers.add_parser("schema", help="Show schema for a table or CSV file")
    schema_parser.add_argument("source_id", help="Source ID")
    schema_parser.add_argument("path", help="Table name or CSV file path")

    args = parser.parse_args()
    store = IndexStore(DEFAULT_INDEX_DB_PATH)

    if args.command == "sources":
        _print_json(list_sources())
    elif args.command == "index":
        connector = create_connector(args.source_id)
        indexed_count = Indexer(store).index_source(connector)
        _print_json({"source_id": args.source_id, "indexed_documents": indexed_count})
    elif args.command == "search":
        results = SearchService(store).search(args.query, limit=args.limit)
        _print_json(results)
    elif args.command == "schema":
        connector = create_connector(args.source_id)
        _print_json(connector.get_schema(args.path).to_dict())


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

