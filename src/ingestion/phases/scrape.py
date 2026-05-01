from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from ingestion.config import BACKOFF_SECONDS, DEFAULT_TIMEOUT_SECONDS, MAX_RETRIES


@dataclass
class ScrapeResult:
    source_url: str
    fetched_at: str
    http_status: int | None
    final_url: str | None
    latency_ms: int
    html: str | None
    error: str | None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_url(url: str) -> ScrapeResult:
    headers = {
        "User-Agent": "mf-faq-rag-scraper/1.0 (+https://github.com/actions)",
        "Accept": "text/html,application/xhtml+xml",
    }

    last_error: str | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        start = time.perf_counter()
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                allow_redirects=True,
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            return ScrapeResult(
                source_url=url,
                fetched_at=_utc_now_iso(),
                http_status=response.status_code,
                final_url=response.url,
                latency_ms=latency_ms,
                html=response.text if response.ok else None,
                error=None if response.ok else f"HTTP {response.status_code}",
            )
        except requests.RequestException as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
            else:
                return ScrapeResult(
                    source_url=url,
                    fetched_at=_utc_now_iso(),
                    http_status=None,
                    final_url=None,
                    latency_ms=latency_ms,
                    html=None,
                    error=last_error,
                )

    return ScrapeResult(
        source_url=url,
        fetched_at=_utc_now_iso(),
        http_status=None,
        final_url=None,
        latency_ms=0,
        html=None,
        error=last_error or "Unknown error",
    )

