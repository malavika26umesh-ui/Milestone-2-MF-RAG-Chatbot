# Deployment Plan: MF FAQ Assistant

This document outlines the strategy for deploying the Mutual Fund FAQ Assistant into a production-grade distributed environment.

## 1. Architecture Overview

The system is split into three main components:
- **Ingestion Scheduler**: Automates daily data updates.
- **Backend API**: Serves retrieval and generation logic.
- **Frontend UI**: Provides the user interface.

| Component | Platform | Primary Responsibility |
| :--- | :--- | :--- |
| **Scheduler** | GitHub Actions | Daily scraping, embedding, and upserting to Chroma Cloud. |
| **Backend** | Render | FastAPI server handling RAG queries and thread management. |
| **Frontend** | Vercel | Next.js application for a premium user experience. |
| **Vector DB** | Chroma Cloud | Managed vector storage (External). |
| **Relational DB**| Render Postgres | Persistent storage for chat threads and history. |

---

## 2. Environment Variables (Secrets)

Ensure the following secrets are configured across platforms:

| Variable | Description | Required On |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | API Key for Llama-3.1-8b generation. | Render |
| `CHROMA_HOST` | Host URL for Chroma Cloud. | Render, GitHub Actions |
| `CHROMA_API_KEY` | Auth key for Chroma Cloud. | Render, GitHub Actions |
| `CHROMA_TENANT` | Chroma tenant ID. | Render, GitHub Actions |
| `CHROMA_DATABASE` | Chroma database name. | Render, GitHub Actions |
| `DATABASE_URL` | PostgreSQL connection string (replacing SQLite). | Render |
| `NEXT_PUBLIC_API_URL`| The public URL of the Render backend. | Vercel |

---

## 3. Frontend Deployment (Vercel)

1. **Connect Repository**: Link your GitHub repo to Vercel.
2. **Framework Preset**: Select `Next.js`.
3. **Root Directory**: Set to `web`.
4. **Environment Variables**: Add `NEXT_PUBLIC_API_URL` (e.g., `https://mf-api.onrender.com`).
5. **Build & Deploy**: Vercel will automatically handle the build and provide a production URL.

---

## 4. Backend Deployment (Render)

1. **Create Web Service**: Connect your GitHub repo.
2. **Environment**: `Python 3`.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn -k uvicorn.workers.UvicornWorker runtime.phase_9_api.app:app --bind 0.0.0.0:$PORT`
5. **Health Check**: Set path to `/api/health`.
6. **Database (Critical)**: Create a **Render PostgreSQL** instance and set the `DATABASE_URL` env var. The `ThreadManager` should be updated to use SQLAlchemy/Postgres for production persistence.

---

## 5. Scheduler Configuration (GitHub Actions)

Create `.github/workflows/ingest.yml`:

```yaml
name: Daily Ingestion Pipeline
on:
  schedule:
    - cron: '15 3 * * *' # 09:15 IST
  workflow_dispatch: # Allows manual trigger

jobs:
  ingest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run Ingestion
        env:
          PYTHONPATH: src
          CHROMA_HOST: ${{ secrets.CHROMA_HOST }}
          CHROMA_API_KEY: ${{ secrets.CHROMA_API_KEY }}
          CHROMA_TENANT: ${{ secrets.CHROMA_TENANT }}
          CHROMA_DATABASE: ${{ secrets.CHROMA_DATABASE }}
        run: python -m ingestion.run_ingestion
```

---

## 6. Post-Deployment Verification

1. **Health Check**: Access `https://your-backend.onrender.com/api/health`.
2. **CORS Check**: Ensure the Render URL is allowlisted in the API CORS settings.
3. **Daily Run**: Verify the first GitHub Action run produces a report in the `data/reports` directory (or logs to a monitoring tool).
