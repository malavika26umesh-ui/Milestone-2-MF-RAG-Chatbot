import argparse
import sys
from runtime.phase_8_threads.thread_manager import ThreadManager

def main():
    parser = argparse.ArgumentParser(description="MF FAQ Threaded Chat CLI (Phase 8)")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # new-thread
    subparsers.add_parser("new-thread", help="Create a new chat thread.")
    
    # list-threads
    subparsers.add_parser("list-threads", help="List all chat threads.")
    
    # say
    say_parser = subparsers.add_parser("say", help="Send a message to a thread.")
    say_parser.add_argument("thread_id", type=str, help="UUID of the thread.")
    say_parser.add_argument("message", type=str, help="Your message.")
    
    # history
    hist_parser = subparsers.add_parser("history", help="Show history for a thread.")
    hist_parser.add_argument("thread_id", type=str, help="UUID of the thread.")
    
    args = parser.parse_args()
    
    manager = ThreadManager()
    
    if args.command == "new-thread":
        tid = manager.create_thread()
        print(f"Created new thread: {tid}")
        
    elif args.command == "list-threads":
        threads = manager.list_threads()
        if not threads:
            print("No threads found.")
        else:
            for t in threads:
                print(f"{t['id']} (Created: {t['created_at']})")
                
    elif args.command == "say":
        print(f"Processing message in thread {args.thread_id}...")
        response = manager.post_message(args.thread_id, args.message)
        print("\n" + "="*50)
        print("ASSISTANT:")
        print("="*50 + "\n")
        print(response)
        print("\n" + "="*50)
        
    elif args.command == "history":
        history = manager.get_thread_history(args.thread_id)
        if not history:
            print(f"No history found for thread {args.thread_id}")
        else:
            print(f"\n--- History for {args.thread_id} ---")
            for h in history:
                print(f"[{h['timestamp']}] {h['role'].upper()}: {h['content']}")
                
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
