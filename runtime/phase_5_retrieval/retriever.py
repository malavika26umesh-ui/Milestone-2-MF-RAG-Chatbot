import json
import pickle
from pathlib import Path
from typing import Any

import chromadb
from chromadb import CloudClient
from sentence_transformers import SentenceTransformer

from ingestion.config import (
    CHROMA_API_KEY,
    CHROMA_COLLECTION_NAME,
    CHROMA_DATABASE,
    CHROMA_HOST,
    CHROMA_TENANT,
    BM25_INDEX_DIR,
    EMBEDDING_MODEL_ID,
)
from runtime.phase_5_retrieval.utils import normalize_query, detect_scheme


class MFRetriever:
    def __init__(self, run_id: str | None = None):
        """
        Initializes the hybrid retriever.
        :param run_id: Optional Run ID to load specific BM25 index. If None, finds the latest.
        """
        self.run_id = run_id or self._find_latest_run_id()
        
        # 1. Initialize BGE Model
        print(f"Loading embedding model: {EMBEDDING_MODEL_ID}...")
        self.model = SentenceTransformer(EMBEDDING_MODEL_ID)
        
        # 2. Initialize Chroma Cloud Client
        print(f"Connecting to Chroma Cloud (Tenant: {CHROMA_TENANT}, DB: {CHROMA_DATABASE})")
        self.chroma_client = chromadb.CloudClient(
            tenant=CHROMA_TENANT,
            database=CHROMA_DATABASE,
            api_key=CHROMA_API_KEY
        )
        self.collection = self.chroma_client.get_collection(name=CHROMA_COLLECTION_NAME)
        
        # 3. Load BM25 Index & Mapping
        self.bm25 = None
        self.mapping = None
        if self.run_id:
            self._load_lexical_index(self.run_id)

    def _find_latest_run_id(self) -> str | None:
        if not BM25_INDEX_DIR.exists():
            return None
        pickles = sorted(BM25_INDEX_DIR.glob("bm25_*.pkl"))
        if not pickles:
            return None
        # Extract run_id from filename (e.g., bm25_20260418T123808Z.pkl)
        return pickles[-1].stem.split("_", 1)[1]

    def _load_lexical_index(self, run_id: str):
        try:
            bm25_path = BM25_INDEX_DIR / f"bm25_{run_id}.pkl"
            mapping_path = BM25_INDEX_DIR / f"mapping_{run_id}.json"
            
            if bm25_path.exists() and mapping_path.exists():
                print(f"Loading BM25 index for run {run_id}...")
                with bm25_path.open("rb") as f:
                    self.bm25 = pickle.load(f)
                with mapping_path.open("r", encoding="utf-8") as f:
                    self.mapping = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load lexical index: {e}")

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """
        Performs retrieval and merges by source_url as per §5.2.
        """
        normalized_q = normalize_query(query)
        scheme_filter = detect_scheme(normalized_q)
        
        if scheme_filter:
            print(f"Detected scheme filter: {scheme_filter}")
        
        # 1. Dense Search
        query_text = f"Represent this sentence: {normalized_q}"
        query_embedding = self.model.encode(query_text, normalize_embeddings=True).tolist()
        
        where_clause = {"scheme_id": scheme_filter} if scheme_filter else None
        
        dense_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max(k * 2, 20),
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
        
        # 2. Hybrid Merging & Source-level Grouping
        # We use a dict keyed by source_url to merge chunks
        merged_sources = {}
        
        if dense_results["ids"]:
            for i in range(len(dense_results["ids"][0])):
                cid = dense_results["ids"][0][i]
                meta = dense_results["metadatas"][0][i]
                doc = dense_results["documents"][0][i]
                dist = dense_results["distances"][0][i]
                url = meta.get("source_url")
                
                if not url:
                    continue
                
                score = 1.0 - (dist / 2.0)
                
                if url not in merged_sources:
                    merged_sources[url] = {
                        "source_url": url,
                        "scheme_id": meta.get("scheme_id"),
                        "fetched_at": meta.get("fetched_at"),
                        "chunks": [],
                        "max_score": score
                    }
                
                merged_sources[url]["chunks"].append({
                    "content": doc,
                    "score": score,
                    "chunk_index": meta.get("chunk_index", 0)
                })
                merged_sources[url]["max_score"] = max(merged_sources[url]["max_score"], score)

        # 3. Final Formatting
        # Sort sources by their best chunk score
        sorted_sources = sorted(merged_sources.values(), key=lambda x: x["max_score"], reverse=True)
        
        # Format for Generation Layer (§6)
        # We return a list of "merged" chunks where each item is one source
        final_output = []
        for src in sorted_sources[:k]:
            # Sort chunks within source by chunk_index to maintain document flow
            src["chunks"].sort(key=lambda x: x["chunk_index"])
            combined_content = "\n\n".join([c["content"] for c in src["chunks"]])
            
            final_output.append({
                "content": combined_content,
                "metadata": {
                    "source_url": src["source_url"],
                    "scheme_id": src["scheme_id"],
                    "fetched_at": src["fetched_at"]
                },
                "score": src["max_score"]
            })
            
        return final_output
