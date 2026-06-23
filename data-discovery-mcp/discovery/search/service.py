from __future__ import annotations

import re
from typing import Any, Dict, List

from discovery.index.store import IndexStore


class SearchService:
    """Case-insensitive keyword search over indexed discovery documents."""

    def __init__(self, store: IndexStore) -> None:
        self.store = store

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        terms = self._terms(query)
        if not terms:
            return []

        scored_results = []
        for document in self.store.list_documents():
            score = self._score(document, terms)
            if score > 0:
                result = dict(document)
                result["score"] = score
                scored_results.append(result)

        scored_results.sort(
            key=lambda result: (
                -result["score"],
                result["source_id"],
                result["object_type"],
                result["path"],
            )
        )
        return scored_results[:limit]

    @staticmethod
    def _terms(query: str) -> List[str]:
        return [term.lower() for term in re.findall(r"[A-Za-z0-9_]+", query)]

    @staticmethod
    def _score(document: Dict[str, Any], terms: List[str]) -> int:
        title = document["title"].lower()
        path = document["path"].lower()
        text = document["text"].lower()

        score = 0
        for term in terms:
            score += title.count(term) * 5
            score += path.count(term) * 3
            score += text.count(term)
        return score

