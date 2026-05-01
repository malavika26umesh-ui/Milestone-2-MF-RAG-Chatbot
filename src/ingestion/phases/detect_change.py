from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ingestion.config import STATE_DIR


STATE_FILE = STATE_DIR / "content_hashes.json"


def _load_state() -> dict[str, str]:
    if not STATE_FILE.exists():
        return {}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def _save_state(state: dict[str, str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def detect_changes(parsed_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    previous = _load_state()
    changed_items: list[dict[str, Any]] = []
    changed_urls: list[str] = []
    next_state = dict(previous)

    for item in parsed_items:
        url = item["source_url"]
        parsed_hash = item.get("parsed_content_hash")
        if not parsed_hash:
            continue

        if previous.get(url) != parsed_hash:
            changed_items.append(item)
            changed_urls.append(url)

        next_state[url] = parsed_hash

    _save_state(next_state)
    return changed_items, changed_urls


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

