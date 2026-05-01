from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from typing import Any

from bs4 import BeautifulSoup

from ingestion.phases.scrape import ScrapeResult


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_whitespace(match.group(1))
    return None


def _collect_label_value_lines(soup: BeautifulSoup) -> list[str]:
    lines: list[str] = []

    # Generic table extraction, useful for key-value UI tables.
    for row in soup.find_all("tr"):
        cells = [normalize_whitespace(c.get_text(" ", strip=True)) for c in row.find_all(["th", "td"])]
        cells = [c for c in cells if c]
        if len(cells) >= 2:
            lines.append(f"{cells[0]}: {cells[1]}")

    # Common key/value blocks rendered as list items or divs.
    for tag in soup.find_all(["li", "div", "span"]):
        text = normalize_whitespace(tag.get_text(" ", strip=True))
        if ":" in text and len(text) < 220:
            lines.append(text)

    # De-duplicate while keeping stable order.
    deduped: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if line not in seen:
            seen.add(line)
            deduped.append(line)
    return deduped


def extract_key_metrics(soup: BeautifulSoup, combined_text: str) -> dict[str, str | None]:
    lines = _collect_label_value_lines(soup)
    searchable = "\n".join(lines + [combined_text])

    return {
        "nav": _first_match(
            [
                r"\bnav\b.*?(?:₹|rs\.?|inr|is|:)\s*([0-9,]+\.[0-9]+)",
                r"\bnet\s+asset\s+value\b.*?(?:₹|rs\.?|inr|is|:)\s*([0-9,]+\.[0-9]+)",
                r"\bnav\b[^0-9]{0,20}([0-9,]+\.[0-9]+)",
            ],
            searchable,
        ),
        "minimum_sip": _first_match(
            [
                r"\bminimum\s+sip\b[^0-9]{0,20}((?:rs\.?|inr)?\s*[0-9,]+)",
                r"\bmin(?:imum)?\s+installment\b[^0-9]{0,20}((?:rs\.?|inr)?\s*[0-9,]+)",
            ],
            searchable,
        ),
        "fund_size": _first_match(
            [
                r"\bfund\s+size\b[^0-9]{0,20}((?:rs\.?|inr)?\s*[0-9,]+(?:\.[0-9]+)?\s*(?:cr|crore|lakh)?)",
                r"\baum\b[^0-9]{0,20}((?:rs\.?|inr)?\s*[0-9,]+(?:\.[0-9]+)?\s*(?:cr|crore|lakh)?)",
            ],
            searchable,
        ),
        "expense_ratio": _first_match(
            [
                r"\bexpense\s+ratio\b[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?\s*%)",
                r"\bter\b[^0-9]{0,20}([0-9]+(?:\.[0-9]+)?\s*%)",
            ],
            searchable,
        ),
        "rating": _first_match(
            [
                r"\brating\b[^0-9]{0,20}([0-5](?:\.[0-9])?\s*/\s*5)",
                r"\brating\b[^0-9]{0,20}([1-5]\s*star)",
            ],
            searchable,
        ),
    }


def parse_html(scrape_result: ScrapeResult) -> dict[str, Any]:
    if not scrape_result.html:
        return {
            "source_url": scrape_result.source_url,
            "fetched_at": scrape_result.fetched_at,
            "http_status": scrape_result.http_status,
            "parse_warnings": ["empty_html"],
            "sections": [],
            "raw_html_hash": None,
            "parsed_content_hash": None,
            "extracted_fields": {
                "nav": None,
                "minimum_sip": None,
                "fund_size": None,
                "expense_ratio": None,
                "rating": None,
            },
        }

    soup = BeautifulSoup(scrape_result.html, "html.parser")
    for bad_tag in soup(["script", "style", "noscript"]):
        bad_tag.decompose()

    title = normalize_whitespace(soup.title.get_text()) if soup.title else "Untitled"
    paragraphs = [
        normalize_whitespace(p.get_text(" ", strip=True))
        for p in soup.find_all("p")
        if normalize_whitespace(p.get_text(" ", strip=True))
    ]

    # Keep top N paragraphs to reduce noise and keep deterministic payload size.
    top_paragraphs = paragraphs[:120]
    combined_text = "\n".join(top_paragraphs)
    extracted_fields = extract_key_metrics(soup, combined_text)

    raw_hash = hashlib.sha256(scrape_result.html.encode("utf-8")).hexdigest()
    parsed_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()

    sections = []
    if top_paragraphs:
        sections.append(
            {
                "title": title,
                "section_type": "scheme-page",
                "text": combined_text,
            }
        )

    warnings = [] if sections else ["no_paragraph_content"]
    missing_metrics = [k for k, v in extracted_fields.items() if not v]
    if missing_metrics:
        warnings.append(f"missing_metrics:{','.join(missing_metrics)}")

    return {
        **asdict(scrape_result),
        "raw_html_hash": raw_hash,
        "parsed_content_hash": parsed_hash,
        "sections": sections,
        "extracted_fields": extracted_fields,
        "parse_warnings": warnings,
    }

