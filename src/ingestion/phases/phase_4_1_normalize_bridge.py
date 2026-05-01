from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from ingestion.config import NORMALIZED_DIR
from ingestion.phases.detect_change import write_json


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def _extract_scheme_name(item: dict) -> str:
    title = ""
    sections = item.get("sections") or []
    if sections:
        title = str(sections[0].get("title") or "")
    if title:
        return title
    return _slug_from_url(item["source_url"]).replace("-", " ").title()


def _build_normalized_text(item: dict) -> str:
    sections = item.get("sections") or []
    parts: list[str] = []
    for section in sections:
        title = section.get("title")
        text = section.get("text")
        if title:
            parts.append(str(title).strip())
        if text:
            parts.append(str(text).strip())
    return "\n\n".join([p for p in parts if p]).strip()


def run_phase_4_1_normalize_bridge(changed_items: list[dict], run_id: str) -> dict:
    run_dir = NORMALIZED_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    outputs: list[dict] = []
    for item in changed_items:
        source_url = item["source_url"]
        scheme_id = _slug_from_url(source_url)
        text = _build_normalized_text(item)
        text_path = run_dir / f"{scheme_id}.txt"
        text_path.write_text(text, encoding="utf-8")

        parsed = urlparse(source_url)
        facts = {
            "source_url": source_url,
            "source_type": "groww_scheme_page",
            "scheme_id": scheme_id,
            "scheme_name": _extract_scheme_name(item),
            "amc": "HDFC Mutual Fund",
            "fetched_at": item.get("fetched_at"),
            "content_hash": item.get("parsed_content_hash"),
            "source_domain": parsed.netloc,
            "extracted_fields": item.get("extracted_fields", {}),
        }
        facts_path = run_dir / f"{scheme_id}.scheme_facts.json"
        write_json(facts_path, facts)

        outputs.append(
            {
                "source_url": source_url,
                "scheme_id": scheme_id,
                "text_path": str(text_path),
                "facts_path": str(facts_path),
                "char_count": len(text),
            }
        )

    manifest = {
        "run_id": run_id,
        "phase": "4.1_normalize_bridge",
        "output_count": len(outputs),
        "outputs": outputs,
    }
    write_json(run_dir / "phase_4_1_manifest.json", manifest)
    return manifest

