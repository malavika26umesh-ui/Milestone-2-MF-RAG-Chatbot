from __future__ import annotations

from urllib.parse import urlparse

import yaml

from ingestion.config import ALLOWED_HOST, SOURCES_FILE


def load_sources() -> list[str]:
    if not SOURCES_FILE.exists():
        raise FileNotFoundError(f"Missing sources file: {SOURCES_FILE}")

    data = yaml.safe_load(SOURCES_FILE.read_text(encoding="utf-8")) or {}
    urls = data.get("sources", [])
    if not isinstance(urls, list) or not urls:
        raise ValueError("sources.yaml must contain a non-empty `sources` list.")

    validated: list[str] = []
    for url in urls:
        if not isinstance(url, str):
            raise ValueError("Every source entry must be a URL string.")
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != ALLOWED_HOST:
            raise ValueError(f"URL not allowlisted: {url}")
        validated.append(url.strip())

    return validated

