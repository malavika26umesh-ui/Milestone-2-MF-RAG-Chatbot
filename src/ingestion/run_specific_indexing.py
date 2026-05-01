import sys
import os
from pathlib import Path

# Add src to sys.path so we can import ingestion
sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.phases.phase_4_3_vector_index import run_phase_4_3_vector_index
from ingestion.phases.phase_4_4_indexing import run_phase_4_4_indexing
from ingestion.config import CHROMA_HOST, CHROMA_API_KEY

def main():
    # Last successful run ID that produced chunks
    run_id = "20260418T123808Z"
    
    # Existing manifest for run 20260418T123808Z
    phase_4_2_manifest = {
        "run_id": run_id,
        "chunks_path": f"D:/M2/data/chunked/{run_id}/chunks.jsonl",
        "embeddings_path": f"D:/M2/data/chunked/{run_id}/embeddings.jsonl"
    }

    print(f"--- Force running indexing for Run ID: {run_id} ---")
    print(f"Configuration: HOST={CHROMA_HOST}, API_KEY_SET={bool(CHROMA_API_KEY)}")
    
    # Run Phase 4.3 (Vector Index)
    print("\n[Phase 4.3] Vector Indexing (Chroma Online Push)...")
    import socket
    from ingestion.config import CHROMA_PORT
    try:
        # Quick connection test to avoid hanging
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Checking if {CHROMA_HOST}:{CHROMA_PORT} is reachable...")
        result = sock.connect_ex((CHROMA_HOST, CHROMA_PORT))
        if result == 0:
            print("Host is reachable. Proceeding with push...")
            res_4_3 = run_phase_4_3_vector_index(phase_4_2_manifest, run_id)
            print(f"Result: {res_4_3}")
        else:
            print(f"Error: {CHROMA_HOST}:{CHROMA_PORT} is not reachable (connect_ex returned {result}). Skipping Phase 4.3.")
        sock.close()
    except Exception as e:
        print(f"Error in Phase 4.3 connection attempt: {e}")

    # Run Phase 4.4 (BM25 & Doc Store)
    print("\n[Phase 4.4] BM25 Indexing & Doc Store Storage...")
    try:
        res_4_4 = run_phase_4_4_indexing(phase_4_2_manifest, run_id)
        print(f"Result: {res_4_4}")
    except Exception as e:
        print(f"Error in Phase 4.4: {e}")

    print("\n--- Indexing Process Complete ---")

if __name__ == "__main__":
    main()
