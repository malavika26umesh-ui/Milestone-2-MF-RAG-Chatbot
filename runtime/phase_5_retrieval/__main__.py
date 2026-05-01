import argparse
import sys
from runtime.phase_5_retrieval.retriever import MFRetriever

def main():
    parser = argparse.ArgumentParser(description="MF FAQ Retrieval CLI (Phase 5)")
    parser.add_argument("query", type=str, help="The user query to retrieve context for.")
    parser.add_argument("--k", type=int, default=5, help="Number of chunks to retrieve.")
    parser.add_argument("--run-id", type=str, help="Specific Run ID for BM25 index.")
    
    args = parser.parse_args()
    
    try:
        retriever = MFRetriever(run_id=args.run_id)
        results = retriever.retrieve(args.query, k=args.k)
        
        print(f"\n--- Top {len(results)} Merged Sources for: '{args.query}' ---\n")
        for i, res in enumerate(results):
            meta = res["metadata"]
            print(f"[{i+1}] Best Score: {res['score']:.4f} | Scheme: {meta.get('scheme_id')}")
            print(f"URL: {meta.get('source_url')}")
            print(f"Fetched At: {meta.get('fetched_at')}")
            # Show snippet of the combined content
            snippet = res['content'][:300].replace('\n', ' ')
            print(f"Content Snippet: {snippet}...")
            print("-" * 60)
            
        if results:
            print(f"\nPrimary Citation URL: {results[0]['metadata']['source_url']}")
            
    except Exception as e:
        print(f"Error during retrieval: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
