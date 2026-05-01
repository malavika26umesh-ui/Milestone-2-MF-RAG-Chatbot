from __future__ import annotations

import json
import pickle
import shutil
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from ingestion.config import BM25_INDEX_DIR, DOC_STORE_DIR, PARSED_DIR
from ingestion.phases.detect_change import write_json


def _tokenize(text: str) -> list[str]:
    # Simple whitespace + lowercase tokenization for BM25
    # For better results, one could use a proper stemmer or tokenizer
    return text.lower().split()


def run_phase_4_4_indexing(phase_4_2_manifest: dict, run_id: str) -> dict:
    chunks_path = Path(phase_4_2_manifest.get("chunks_path", ""))
    
    if not chunks_path.is_file():
        return {
            "run_id": run_id,
            "phase": "4.4_indexing",
            "status": "skipped_no_chunks",
        }

    # 1. BM25 Indexing
    chunks: list[dict] = []
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))

    if not chunks:
        return {
            "run_id": run_id,
            "phase": "4.4_indexing",
            "status": "skipped_empty_chunks",
        }

    corpus = [chunk["chunk_text"] for chunk in chunks]
    tokenized_corpus = [_tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    BM25_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    bm25_path = BM25_INDEX_DIR / f"bm25_{run_id}.pkl"
    with bm25_path.open("wb") as f:
        pickle.dump(bm25, f)
    
    # Also save a mapping of index to chunk_id for retrieval
    mapping_path = BM25_INDEX_DIR / f"mapping_{run_id}.json"
    mapping = {i: chunk["chunk_id"] for i, chunk in enumerate(chunks)}
    write_json(mapping_path, mapping)

    # 2. Document Store (Traceability)
    DOC_STORE_DIR.mkdir(parents=True, exist_ok=True)
    # Collect unique scheme_ids from chunks to identify which parsed files to store
    scheme_ids = {chunk["scheme_id"] for chunk in chunks}
    stored_docs = []
    for scheme_id in scheme_ids:
        # Find the latest parsed JSON for this scheme
        # In run_ingestion.py, parsed JSONs are stored as PARSED_DIR / slug / f"{run_stamp}.json"
        scheme_parsed_dir = PARSED_DIR / scheme_id
        if scheme_parsed_dir.exists():
            # Get the most recent one (or matching run_id if possible)
            # For simplicity, we'll try to match run_id if it's the run_stamp
            match = list(scheme_parsed_dir.glob(f"{run_id}.json"))
            if not match:
                # Fallback to latest
                match = sorted(scheme_parsed_dir.glob("*.json"))
            
            if match:
                latest_parsed = match[-1]
                dest = DOC_STORE_DIR / f"{scheme_id}_{run_id}.json"
                shutil.copy2(latest_parsed, dest)
                stored_docs.append(str(dest))

    manifest = {
        "run_id": run_id,
        "phase": "4.4_indexing",
        "bm25_path": str(bm25_path),
        "mapping_path": str(mapping_path),
        "chunk_count": len(chunks),
        "stored_docs_count": len(stored_docs),
        "status": "success",
    }
    
    run_dir = chunks_path.parent
    write_json(run_dir / "indexing_manifest.json", manifest)
    
    return manifest
