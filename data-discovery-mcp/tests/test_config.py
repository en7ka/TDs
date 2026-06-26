import json
from pathlib import Path

from discovery.config import load_sources


def test_load_sources_from_json_config(tmp_path: Path) -> None:
    config_path = tmp_path / "sources.json"
    config_path.write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "local_csv",
                        "kind": "csv",
                        "path": "data",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    sources = load_sources(config_path)

    assert len(sources) == 1
    assert sources[0].source_id == "local_csv"
    assert sources[0].kind == "csv"
    assert sources[0].path == tmp_path / "data"
