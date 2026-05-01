import uvicorn
import argparse

def main():
    parser = argparse.ArgumentParser(description="MF FAQ Assistant API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on.")
    
    args = parser.parse_args()
    
    print(f"Starting server on {args.host}:{args.port}...")
    uvicorn.run("runtime.phase_9_api.app:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
