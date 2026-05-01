from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Try to load .env from root or src/
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / "src" / ".env")



BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PARSED_DIR = DATA_DIR / "parsed"
NORMALIZED_DIR = DATA_DIR / "normalized"
CHUNKED_DIR = DATA_DIR / "chunked"
STATE_DIR = DATA_DIR / "state"
REPORTS_DIR = DATA_DIR / "reports"

SOURCES_FILE = BASE_DIR / "sources.yaml"
ALLOWED_HOST = "groww.in"

DEFAULT_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", "20"))
MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
BACKOFF_SECONDS = float(os.getenv("SCRAPER_BACKOFF_SECONDS", "1.5"))

# Phase 4.2 chunking/embedding configuration
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-small-en-v1.5")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
EMBED_BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "32"))
CHUNK_TARGET_TOKENS = int(os.getenv("CHUNK_TARGET_TOKENS", "400"))
CHUNK_MAX_TOKENS = int(os.getenv("CHUNK_MAX_TOKENS", "460"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "50"))

# Phase 4.3 vector index configuration
INGEST_CHROMA_DIR = Path(os.getenv("INGEST_CHROMA_DIR", str(DATA_DIR / "chroma")))
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "mutual_fund_faqs")
CHROMA_HOST = os.getenv("CHROMA_HOST") or None
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "443"))
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY") or None
CHROMA_TENANT = os.getenv("CHROMA_TENANT") or "default"
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE") or "default"

# Phase 4.4 BM25 and Doc Store configuration
BM25_INDEX_DIR = DATA_DIR / "bm25"
DOC_STORE_DIR = DATA_DIR / "doc_store"

