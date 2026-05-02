from __future__ import annotations
import json
from pathlib import Path
from sqlalchemy.orm import Session
from runtime.db.models import SessionLocal, FundDocument, init_db

def run_phase_4_5_db_sync(changed_items: list[dict], run_id: str) -> dict:
    """
    Syncs the latest normalized fund data to the production database.
    This ensures the backend can access the 'Ground Truth' source text 
    without needing local JSON files.
    """
    if not changed_items:
        return {"run_id": run_id, "phase": "4.5_db_sync", "status": "skipped_no_changes"}

    print(f"Phase 4.5: Syncing {len(changed_items)} changed documents to Database...")
    init_db()
    session = SessionLocal()
    
    synced_count = 0
    try:
        for item in changed_items:
            scheme_id = item.get("scheme_id")
            if not scheme_id:
                continue
                
            # Prepare normalized content from sections
            sections = item.get("sections", [])
            full_content = "\n\n".join([f"## {s['title']}\n{s['content']}" for s in sections])
            
            # Prepare metadata (everything except sections and raw content)
            metadata = {k: v for k, v in item.items() if k not in ["sections", "raw_html"]}
            
            # Upsert into DB
            doc = session.query(FundDocument).filter(FundDocument.scheme_id == scheme_id).first()
            if not doc:
                doc = FundDocument(scheme_id=scheme_id)
                session.add(doc)
            
            doc.scheme_name = item.get("scheme_name")
            doc.source_url = item.get("source_url")
            doc.content = full_content
            doc.metadata_json = metadata
            
            synced_count += 1
            
        session.commit()
    except Exception as e:
        print(f"FAILED to sync to database: {e}")
        session.rollback()
        raise
    finally:
        session.close()

    manifest = {
        "run_id": run_id,
        "phase": "4.5_db_sync",
        "synced_count": synced_count,
        "status": "success",
    }
    return manifest
