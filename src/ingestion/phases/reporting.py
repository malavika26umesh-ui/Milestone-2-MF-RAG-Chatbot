from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_run_report(
    total_sources: int,
    fetched_count: int,
    failed_count: int,
    changed_urls: list[str],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    status = "success"
    if failed_count == total_sources:
        status = "failed"
    elif failed_count > 0:
        status = "partial_success"

    return {
        "run_id": utc_now_compact(),
        "status": status,
        "total_sources": total_sources,
        "fetched_count": fetched_count,
        "failed_count": failed_count,
        "changed_count": len(changed_urls),
        "changed_urls": changed_urls,
        "results": results,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }

