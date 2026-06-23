from pathlib import Path

from discovery.config import create_connector
from discovery.index.indexer import Indexer
from discovery.index.store import IndexStore
from discovery.search.service import SearchService


def test_search_finds_email_order_and_product(tmp_path: Path) -> None:
    store = IndexStore(tmp_path / "index.sqlite")
    indexer = Indexer(store)
    indexer.index_source(create_connector("sqlite_demo"))
    indexer.index_source(create_connector("csv_demo"))

    service = SearchService(store)

    email_results = service.search("email")
    order_results = service.search("order")
    product_results = service.search("product")

    assert email_results
    assert order_results
    assert product_results
    assert any(result["object_type"] == "column" and "email" in result["path"] for result in email_results)
    assert any("orders" in result["path"] or "orders.csv" in result["path"] for result in order_results)
    assert any("products" in result["path"] or "product_id" in result["path"] for result in product_results)
    assert email_results[0]["score"] >= email_results[-1]["score"]

