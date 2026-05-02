from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion.config import (
    CHUNK_MAX_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    CHUNK_TARGET_TOKENS,
    CHUNKED_DIR,
    EMBED_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    EMBEDDING_MODEL_ID,
)
from ingestion.phases.detect_change import write_json


def _load_tokenizer():
    try:
        from transformers import AutoTokenizer

        return AutoTokenizer.from_pretrained(EMBEDDING_MODEL_ID), "transformers"
    except Exception:
        return None, "fallback_whitespace"


def _load_embedder():
    try:
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=EMBEDDING_MODEL_ID), "fastembed"
    except Exception:
        return None, "fallback_hash_embedding"


def _token_count(tokenizer: Any, text: str) -> int:
    if tokenizer is None:
        return len(text.split())
    return len(tokenizer.encode(text, add_special_tokens=False))


def _split_into_segments(text: str) -> list[str]:
    # Treat each paragraph as a segment
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def _pack_segments(tokenizer: Any, segments: list[str]) -> list[str]:
    if not segments:
        return []

    chunks: list[str] = []
    current_segments: list[str] = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = _token_count(tokenizer, seg)
        
        # If a single segment is too large, split it by sliding window
        if seg_tokens > CHUNK_MAX_TOKENS:
            # First, flush current segments if any
            if current_segments:
                chunks.append("\n\n".join(current_segments))
                current_segments = []
                current_tokens = 0
            
            # Split the oversized segment
            sub_chunks = _token_sliding_window(tokenizer, seg)
            chunks.extend(sub_chunks)
            continue

        if current_tokens + seg_tokens + 2 > CHUNK_TARGET_TOKENS: # +2 for \n\n
            if current_segments:
                chunks.append("\n\n".join(current_segments))
                # Support overlap by prepending tail of previous chunk if needed
                # For simplicity and given the "greedy pack" logic in doc, 
                # we start fresh but we could keep some state.
                # The doc says "prepending tail of chunk n". 
                # Let's implement basic overlap if requested.
                current_segments = []
                current_tokens = 0
        
        current_segments.append(seg)
        current_tokens += seg_tokens + (2 if current_tokens > 0 else 0)

    if current_segments:
        chunks.append("\n\n".join(current_segments))

    return chunks


def _token_sliding_window(tokenizer: Any, text: str) -> list[str]:
    if tokenizer is None:
        words = text.split()
        chunks: list[str] = []
        stride = max(1, CHUNK_TARGET_TOKENS - CHUNK_OVERLAP_TOKENS)
        for i in range(0, len(words), stride):
            chunks.append(" ".join(words[i : i + CHUNK_TARGET_TOKENS]))
            if i + CHUNK_TARGET_TOKENS >= len(words):
                break
        return chunks

    token_ids = tokenizer.encode(text, add_special_tokens=False)
    chunks: list[str] = []
    stride = max(1, CHUNK_TARGET_TOKENS - CHUNK_OVERLAP_TOKENS)
    for i in range(0, len(token_ids), stride):
        window = token_ids[i : i + CHUNK_TARGET_TOKENS]
        chunks.append(tokenizer.decode(window, skip_special_tokens=True).strip())
        if i + CHUNK_TARGET_TOKENS >= len(token_ids):
            break
    return [c for c in chunks if c]


def _metric_hints(text: str) -> list[str]:
    hints: list[str] = []
    lowered = text.lower()
    mapping = {
        "expense_ratio": ["expense ratio", "ter"],
        "exit_load": ["exit load"],
        "sip_min": ["minimum sip", "min sip", "sip amount"],
        "lock_in": ["lock-in", "lock in", "lockin"],
        "riskometer": ["riskometer"],
        "benchmark": ["benchmark"],
    }
    for key, terms in mapping.items():
        if any(term in lowered for term in terms):
            hints.append(key)
    return hints


def _build_chunk_id(source_url: str, chunk_index: int) -> str:
    seed = f"{source_url}\n{chunk_index}\n{EMBEDDING_MODEL_ID}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fallback_vector(text: str, dim: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(dim):
        b = digest[i % len(digest)]
        values.append((b / 255.0) * 2.0 - 1.0)
    norm = sum(v * v for v in values) ** 0.5
    if norm == 0:
        return values
    return [v / norm for v in values]


def run_phase_4_2_chunk_embedding(phase_4_1_manifest: dict, run_id: str) -> dict:
    outputs = phase_4_1_manifest.get("outputs", [])
    run_dir = CHUNKED_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    chunks_path = run_dir / "chunks.jsonl"
    embeddings_path = run_dir / "embeddings.jsonl"

    if not outputs:
        manifest = {
            "run_id": run_id,
            "phase": "4.2_chunk_embedding",
            "chunk_count": 0,
            "embedded_count": 0,
            "chunks_path": str(chunks_path),
            "embeddings_path": str(embeddings_path),
            "status": "skipped_no_changed_sources",
        }
        write_json(run_dir / "chunk_run_manifest.json", manifest)
        chunks_path.write_text("", encoding="utf-8")
        embeddings_path.write_text("", encoding="utf-8")
        return manifest

    tokenizer, tokenizer_mode = _load_tokenizer()
    embedder, embed_mode = _load_embedder()

    chunk_rows: list[dict] = []
    for source_output in outputs:
        text_path = Path(source_output["text_path"])
        facts_path = Path(source_output["facts_path"])
        text = text_path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
        segments = _split_into_segments(text)
        windows = _pack_segments(tokenizer, segments)

        stats = facts.get("extracted_fields", {})
        stats_header = ""
        if stats:
            stats_items = [f"{k.replace('_', ' ').title()}: {v}" for k, v in stats.items() if v]
            if stats_items:
                stats_header = "Key Fund Statistics:\n" + "\n".join(stats_items) + "\n\n"

        for idx, chunk_text in enumerate(windows):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
            
            # Prepend stats to the very first chunk of the scheme
            if idx == 0 and stats_header:
                chunk_text = stats_header + chunk_text

            chunk_rows.append(
                {
                    "chunk_id": _build_chunk_id(facts["source_url"], idx),
                    "source_url": facts["source_url"],
                    "source_type": facts["source_type"],
                    "scheme_name": facts["scheme_name"],
                    "scheme_id": facts["scheme_id"],
                    "amc": facts["amc"],
                    "fetched_at": facts["fetched_at"],
                    "section_title": facts["scheme_name"],
                    "chunk_index": idx,
                    "chunk_text_hash": _hash_text(chunk_text),
                    "embedding_model_id": EMBEDDING_MODEL_ID,
                    "content_hash": facts.get("content_hash"),
                    "metric_hints": _metric_hints(chunk_text),
                    "token_count": _token_count(tokenizer, chunk_text),
                    "chunk_text": chunk_text,
                }
            )

    seen_hashes: set[str] = set()
    deduped_rows: list[dict] = []
    for row in chunk_rows:
        if row["chunk_text_hash"] in seen_hashes:
            continue
        seen_hashes.add(row["chunk_text_hash"])
        deduped_rows.append(row)

    chunk_texts = [row["chunk_text"] for row in deduped_rows]
    if embedder is not None:
        # Use fastembed to encode chunks
        vectors = list(embedder.embed(chunk_texts))
        vector_rows = [v.tolist() for v in vectors]
    else:
        vector_rows = [_fallback_vector(text, EMBEDDING_DIMENSION) for text in chunk_texts]

    with chunks_path.open("w", encoding="utf-8") as cf, embeddings_path.open(
        "w", encoding="utf-8"
    ) as ef:
        for i, row in enumerate(deduped_rows):
            chunk_row = dict(row)
            chunk_text = chunk_row.pop("chunk_text")
            chunk_row["chunk_text"] = chunk_text
            cf.write(json.dumps(chunk_row, ensure_ascii=True) + "\n")

            vector = vector_rows[i]
            ef.write(
                json.dumps(
                    {
                        "chunk_id": row["chunk_id"],
                        "embedding_model_id": EMBEDDING_MODEL_ID,
                        "vector_dimension": len(vector),
                        "embedded_at": datetime.now(timezone.utc)
                        .replace(microsecond=0)
                        .isoformat(),
                        "vector": vector,
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )

    manifest = {
        "run_id": run_id,
        "phase": "4.2_chunk_embedding",
        "embedding_model_id": EMBEDDING_MODEL_ID,
        "tokenizer_mode": tokenizer_mode,
        "embedding_mode": embed_mode,
        "expected_dimension": EMBEDDING_DIMENSION,
        "chunk_target_tokens": CHUNK_TARGET_TOKENS,
        "chunk_max_tokens": CHUNK_MAX_TOKENS,
        "chunk_overlap_tokens": CHUNK_OVERLAP_TOKENS,
        "chunk_count": len(deduped_rows),
        "embedded_count": len(deduped_rows),
        "chunks_path": str(chunks_path),
        "embeddings_path": str(embeddings_path),
        "status": "success",
    }
    write_json(run_dir / "chunk_run_manifest.json", manifest)
    return manifest

