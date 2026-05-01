import argparse
import sys
from runtime.phase_5_retrieval.retriever import MFRetriever
from runtime.phase_6_generation.generator import GroqGenerator

def main():
    parser = argparse.ArgumentParser(description="MF FAQ Generation CLI (Phase 6)")
    parser.add_argument("query", type=str, help="The user query to answer.")
    parser.add_argument("--k", type=int, default=3, help="Number of chunks to retrieve for context.")
    parser.add_argument("--model", type=str, default="llama-3.1-8b-instant", help="Groq model ID.")
    
    args = parser.parse_args()
    
    try:
        # 1. Retrieval (Phase 5)
        print(f"Retrieving context for: '{args.query}'...")
        retriever = MFRetriever()
        results = retriever.retrieve(args.query, k=args.k)
        
        if not results:
            print("No relevant context found. Cannot generate answer.")
            sys.exit(0)
            
        # 2. Generation (Phase 6)
        print(f"Generating answer using {args.model}...")
        generator = GroqGenerator(model_id=args.model)
        answer = generator.generate_answer(args.query, results)
        
        print("\n" + "="*50)
        print("ASSISTANT RESPONSE:")
        print("="*50 + "\n")
        print(answer)
        print("\n" + "="*50)
            
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
