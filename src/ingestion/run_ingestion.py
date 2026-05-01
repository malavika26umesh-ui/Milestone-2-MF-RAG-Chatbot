from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from ingestion.config import PARSED_DIR, RAW_DIR, REPORTS_DIR
from ingestion.phases.detect_change import detect_changes, write_json
from ingestion.phases.load_sources import load_sources
from ingestion.phases.normalize import parse_html
from ingestion.phases.phase_4_1_normalize_bridge import run_phase_4_1_normalize_bridge
from ingestion.phases.phase_4_2_chunk_embedding import run_phase_4_2_chunk_embedding
from ingestion.phases.phase_4_3_vector_index import run_phase_4_3_vector_index
from ingestion.phases.phase_4_4_indexing import run_phase_4_4_indexing
from ingestion.phases.reporting import build_run_report, utc_now_compact
from ingestion.phases.scrape import fetch_url


def _slug_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def main() -> int:
    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_stamp = utc_now_compact()

    urls = load_sources()
    print(f"Loaded {len(urls)} URLs from sources.yaml")
    raw_results: list[dict] = []
    parsed_results: list[dict] = []

    for url in urls:
        print(f"Phase 1: Scraping {url}...")
        scrape_result = fetch_url(url)
        slug = _slug_from_url(url)
        raw_payload = {
            "source_url": scrape_result.source_url,
            "fetched_at": scrape_result.fetched_at,
            "http_status": scrape_result.http_status,
            "final_url": scrape_result.final_url,
            "latency_ms": scrape_result.latency_ms,
            "error": scrape_result.error,
        }
        raw_results.append(raw_payload)

        if scrape_result.html:
            raw_html_path = RAW_DIR / slug / f"{run_stamp}.html"
            raw_html_path.parent.mkdir(parents=True, exist_ok=True)
            raw_html_path.write_text(scrape_result.html, encoding="utf-8")

        print(f"Phase 2: Normalizing {slug}...")
        parsed = parse_html(scrape_result)
        parsed_results.append(parsed)
        write_json(PARSED_DIR / slug / f"{run_stamp}.json", parsed)

    print("Phase 3: Detecting content changes...")
    changed_items, changed_urls = detect_changes(parsed_results)
    changed_payload = [
        {
            "source_url": item["source_url"],
            "parsed_content_hash": item.get("parsed_content_hash"),
            "section_count": len(item.get("sections", [])),
        }
        for item in changed_items
    ]
    write_json(REPORTS_DIR / f"changed-items-{run_stamp}.json", changed_payload)
    print(f"Detected changes in {len(changed_urls)} URLs.")
    
    print("Phase 4.1: Running Normalize Bridge...")
    phase_4_1_manifest = run_phase_4_1_normalize_bridge(changed_items=changed_items, run_id=run_stamp)
    
    print("Phase 4.2: Running Chunking & Embedding...")
    phase_4_2_manifest = run_phase_4_2_chunk_embedding(
        phase_4_1_manifest=phase_4_1_manifest, run_id=run_stamp
    )
    
    print("Phase 4.3: Updating Vector Index (Chroma)...")
    phase_4_3_manifest = run_phase_4_3_vector_index(
        phase_4_2_manifest=phase_4_2_manifest, run_id=run_stamp
    )
    
    print("Phase 4.4: Finalizing Indexing...")
    phase_4_4_manifest = run_phase_4_4_indexing(
        phase_4_2_manifest=phase_4_2_manifest, run_id=run_stamp
    )

    failed_count = sum(1 for r in raw_results if r.get("error") is not None)
    fetched_count = len(raw_results) - failed_count
    report = build_run_report(
        total_sources=len(urls),
        fetched_count=fetched_count,
        failed_count=failed_count,
        changed_urls=changed_urls,
        results=raw_results,
    )
    report["started_at"] = started_at
    report["finished_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    report["phase_4_1"] = phase_4_1_manifest
    report["phase_4_2"] = phase_4_2_manifest
    report["phase_4_3"] = phase_4_3_manifest
    report["phase_4_4"] = phase_4_4_manifest

    report_path = REPORTS_DIR / f"run-report-{run_stamp}.json"
    write_json(report_path, report)
    print(f"Ingestion complete. Report: {report_path}")
    print(f"Status: {report['status']} | Changed URLs: {report['changed_count']}")

    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())

