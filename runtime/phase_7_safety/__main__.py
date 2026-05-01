import argparse
import sys
from runtime.phase_7_safety.safety_manager import SafetyManager
from runtime.phase_7_safety.router import QueryRouter

def main():
    parser = argparse.ArgumentParser(description="MF FAQ Safety & Refusal CLI (Phase 7)")
    parser.add_argument("query", type=str, help="The user query.")
    parser.add_argument("--route-only", action="store_true", help="Only show the routing decision.")
    
    args = parser.parse_args()
    
    if args.route_only:
        router = QueryRouter()
        category = router.route(args.query)
        print(f"\nQuery: '{args.query}'")
        print(f"Routing Decision: {category.value.upper()}")
    else:
        manager = SafetyManager()
        answer = manager.answer(args.query)
        print("\n" + "="*50)
        print("FINAL RESPONSE:")
        print("="*50 + "\n")
        print(answer)
        print("\n" + "="*50)

if __name__ == "__main__":
    main()
