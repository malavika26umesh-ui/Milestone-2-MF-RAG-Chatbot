# Mutual Fund FAQ Assistant - Ingestion Services

Aligned with [docs/ragArchitecture.md](file:///d:/M2/docs/ragArchitecture.md). 

## Processing Pipeline
Query-time retrieval (§5) lives in `runtime/phase_5_retrieval/`; generation (§6, Groq) in `runtime/phase_6_generation/`; safety router (§7) in `runtime/phase_7_safety/` (python -m runtime.phase_7_safety recommended).

## Local Configuration
Copy `.env.example` to `.env` in the repo root if you need overrides (optional `INGEST_*`, `GROQ_API_KEY` for runtime). All phase `python -m ingestion...` entrypoints load `.env` automatically. **Do not commit `.env`.**

## Pipeline Phases

| Folder | Phase | Status |
| :--- | :--- | :--- |
| `url_registry/` | §4.1 URL registry | Active — YAML allowlist |
| `phases/phase_4_0_scheduler_scraping/` | §4.0 Scheduler + scraping | Implemented |
| `phases/phase_4_1_normalize/` | §4.1 Normalize HTML | Implemented |
| `phases/phase_4_2_chunk_embedding/` | §4.1 Chunk + embed | Implemented |
| `phases/phase_4_3_vector_index/` | §4.3 Chroma Cloud vector index | Implemented — see [ragArchitecture.md](file:///d:/M2/docs/ragArchitecture.md) §4.3 |

---

## Local Scheduler (Full Pipeline + Log)
To mirror `.github/workflows/ingest.yml` on your machine (all phases in order) and capture stdout/stderr to a timestamped log under `data/logs/`:
```bash
./scripts/run-ingest-local.sh
```

**Optional:** pass a custom log path as the first argument:
```bash
./scripts/run-ingest-local.sh /tmp/my-ingest.log
```

The script uses `.venv/bin/python` when present, otherwise `python3`. It sets `HF_HOME` to `.cache/huggingface` under the repo when unset (same idea as CI). Log lines are prefixed with UTC timestamps for each phase boundary.

### Pruning
After a successful 4.3, the script runs `python -m ingestion.prune_old_runs` so only the latest `run_id` remains under `data/raw/`, `data/normalized/`, and `data/chunked/` (older scrape runs are removed). It also keeps the 20 newest `data/logs/ingest-*.log` files and deletes older logs. Set `INGEST_PRUNE_SKIP=1` (or true/yes) to skip that step.

**Manual Pruning:**
```bash
python3 -m ingestion.prune_old_runs
python3 -m ingestion.prune_old_runs --dry-run
python3 -m ingestion.prune_old_runs --keep 20260415T150337
python3 -m ingestion.prune_old_runs --log-files 0   # do not prune ingest logs
```

### Chroma
Phase 4.3 upserts the current run to Remote Chroma Cloud via `HttpClient`. It manages the collection by upserting new/changed chunks and removing stale ones.

---

## Running Phases Individually

### 1. Run Scrape Locally
From the repository root:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m ingestion.phases.phase_4_0_scheduler_scraping
```
Outputs under `data/raw/<run_id>/`: one `.html` per successful URL, `manifest.json`, and `amc.txt`.

### 2. Run Normalize (Phase 4.1)
```bash
python3 -m ingestion.phases.phase_4_1_normalize
# or: python3 -m ingestion.phases.phase_4_1_normalize --run-id <run_id>
```
Outputs under `data/normalized/<run_id>/`: one `.txt` per scheme, `scheme_facts.json`, `normalize_manifest.json`.

### 3. Chunk + Embed (Phase 4.2)
```bash
python3 -m ingestion.phases.phase_4_2_chunk_embedding
# Add --no-embed to skip local model inference
```
Outputs under `data/chunked/<run_id>/`: `chunks.jsonl`, optional `embeddings.jsonl`, `chunk_run_manifest.json`.

### 4. Chroma index (Phase 4.3)
```bash
python3 -m ingestion.phases.phase_4_3_vector_index
```
Pushes vectors to Remote Chroma Cloud using the configuration in `.env` (`CHROMA_HOST`, `CHROMA_API_KEY`, etc.). See `phase_4_3_vector_index/README.md`.

---

## Environment Variables

| Variable | Purpose |
| :--- | :--- |
| `INGEST_REGISTRY_PATH` | Path to `urls.yaml` (default: `ingest/url_registry/urls.yaml`) |
| `INGEST_RAW_DIR` | Base directory for raw HTML (default: `data/raw`) |
| `INGEST_USER_AGENT` | HTTP User-Agent string |
| `INGEST_RATE_LIMIT_SECONDS` | Delay between requests (default 1.5) |
| `INGEST_TIMEOUT_SECONDS` | Per-request timeout (default 30) |
| `INGEST_NORMALIZED_DIR` | Phase 4.1 output base (default `data/normalized`) |
| `INGEST_REPO_ROOT` | Repo root for default `data/*` paths |
| `INGEST_CHUNKED_DIR` | Phase 4.2 output base (default `data/chunked`) |
| `CHROMA_HOST` | Remote Chroma Cloud Host (e.g., `api.trychroma.com`) |
| `CHROMA_PORT` | Remote Port (default: 443) |
| `CHROMA_API_KEY` | Bearer Token for Authentication |
| `CHROMA_TENANT` | Workspace Tenant (from Chroma Cloud) |
| `CHROMA_DATABASE` | Targeted Database (from Chroma Cloud) |
| `CHROMA_COLLECTION_NAME` | Destination Collection Name |
| `INGEST_CHROMA_DIR` | Local Persist Fallback (default `data/chroma`) |
| `HF_HOME` | Hugging Face model cache dir (optional) |
| `INGEST_PRUNE_SKIP` | If 1/true/yes, skip prune in `run-ingest-local.sh` |

---

## Scheduler (GitHub Actions)
Workflow: `.github/workflows/ingest.yml` — Daily at **09:15 IST** (`03:45 UTC`). Supports manual trigger via Actions UI.

Each run executes in order on a clean checkout (the same `run_id` flows through all stages):
- **Phase 4.0** — Scrape allowlisted URLs → `data/raw/<run_id>/`
- **Phase 4.1** — Normalize HTML → `data/normalized/<run_id>/`
- **Phase 4.2** — Chunk + local BGE embeddings → `data/chunked/<run_id>/`
- **Phase 4.3** — Remote Upsert to Chroma Cloud using repository secrets.

Repository Secrets: `CHROMA_HOST`, `CHROMA_API_KEY`, `CHROMA_TENANT`, `CHROMA_DATABASE`, and optional `INGEST_USER_AGENT`.
