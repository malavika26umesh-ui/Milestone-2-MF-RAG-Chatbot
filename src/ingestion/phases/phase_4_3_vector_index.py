from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from ingestion.config import (
    CHROMA_API_KEY,
    CHROMA_COLLECTION_NAME,
    CHROMA_DATABASE,
    CHROMA_HOST,
    CHROMA_PORT,
    CHROMA_TENANT,
    INGEST_CHROMA_DIR,
)
from ingestion.phases.detect_change import write_json


def run_phase_4_3_vector_index(phase_4_2_manifest: dict, run_id: str) -> dict:
    chunks_path = Path(phase_4_2_manifest.get("chunks_path", ""))
    embeddings_path = Path(phase_4_2_manifest.get("embeddings_path", ""))

    if not chunks_path.is_file() or not embeddings_path.is_file():
        manifest = {
            "run_id": run_id,
            "phase": "4.3_vector_index",
            "status": "skipped_no_input_files",
        }
        return manifest

    # Initialize Chroma Client (Remote or Local)
    if CHROMA_HOST:
        print(f"Connecting to Chroma Cloud (Tenant: {CHROMA_TENANT}, DB: {CHROMA_DATABASE})")
        try:
            # Use CloudClient for Chroma Cloud (api.trychroma.com)
            client = chromadb.CloudClient(
                tenant=CHROMA_TENANT,
                database=CHROMA_DATABASE,
                api_key=CHROMA_API_KEY
            )
            # Verify connectivity
            client.heartbeat()
            print("Successfully connected to Chroma Cloud.")
        except Exception as e:
            print(f"FAILED to connect to Chroma Cloud: {e}")
            raise
    else:
        INGEST_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(INGEST_CHROMA_DIR))

    # Get or create collection
    # Distance metric: cosine (consistent with normalized BGE vectors)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    # Load chunks and embeddings
    chunks: dict[str, dict] = {}
    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                chunks[c["chunk_id"]] = c

    embeddings: list[dict] = []
    with embeddings_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                embeddings.append(json.loads(line))

    # Prepare batch upsert
    ids = []
    vectors = []
    metadatas = []
    documents = []

    for emb in embeddings:
        chunk_id = emb["chunk_id"]
        if chunk_id not in chunks:
            continue
        
        chunk = chunks[chunk_id]
        ids.append(chunk_id)
        vectors.append(emb["vector"])
        documents.append(chunk["chunk_text"])
        
        # Filter metadata for Chroma compatibility (string, int, float, bool)
        metadata = {
            "source_url": chunk["source_url"],
            "scheme_id": chunk["scheme_id"],
            "scheme_name": chunk["scheme_name"],
            "source_type": chunk["source_type"],
            "amc": chunk["amc"],
            "fetched_at": chunk["fetched_at"],
            "chunk_index": chunk["chunk_index"],
            "section_title": chunk.get("section_title") or "",
            "chunk_id": chunk_id,
            "embedding_model_id": emb["embedding_model_id"]
        }
        # Add metric hints as comma-separated string
        if chunk.get("metric_hints"):
            metadata["metric_hints"] = ",".join(chunk["metric_hints"])
        
        metadatas.append(metadata)

    # Upsert in batches to avoid overwhelming memory/network if needed
    # Since it's a local client, we can do it in one or a few goes.
    batch_size = 500
    for i in range(0, len(ids), batch_size):
        end = i + batch_size
        collection.upsert(
            ids=ids[i:end],
            embeddings=vectors[i:end],
            metadatas=metadatas[i:end],
            documents=documents[i:end]
        )

    manifest = {
        "run_id": run_id,
        "phase": "4.3_vector_index",
        "collection_name": CHROMA_COLLECTION_NAME,
        "chroma_dir": str(INGEST_CHROMA_DIR),
        "upserted_count": len(ids),
        "status": "success",
    }
    
    # Write index manifest
    run_dir = chunks_path.parent
    write_json(run_dir / "chroma_index_manifest.json", manifest)
    
    return manifest
