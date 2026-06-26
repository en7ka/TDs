from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from discovery.index.store import IndexStore


class SearchService:
    """Case-insensitive keyword search over indexed discovery documents."""

    def __init__(self, store: IndexStore) -> None:
        self.store = store

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        match_query = self._match_query(query)
        if match_query is None:
            return []
        return self.store.search_documents(match_query, limit=limit)

    @classmethod
    def _match_query(cls, query: str) -> Optional[str]:
        terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_]+", query)]
        if not terms:
            return None
        return " OR ".join(f"{term}*" for term in terms)
