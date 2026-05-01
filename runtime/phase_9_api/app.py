import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from contextlib import asynccontextmanager

from runtime.phase_8_threads.thread_manager import ThreadManager
from runtime.phase_9_api.schemas import MessageCreate, MessageResponse, ThreadResponse, HealthResponse

# Global manager to keep models warm
manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global manager
    print("Initializing RAG models (warm start)...")
    manager = ThreadManager()
    # Trigger lazy init to load models immediately
    manager.safety_manager._lazy_init_rag()
    print("RAG models loaded and ready.")
    yield
    print("Shutting down...")

app = FastAPI(title="MF FAQ Assistant API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, allow all. In production, restrict to port 3001.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/threads", response_model=ThreadResponse)
async def create_thread():
    thread_id = manager.create_thread()
    threads = manager.list_threads()
    # Find the one we just created
    for t in threads:
        if t["id"] == thread_id:
            return t
    raise HTTPException(status_code=500, detail="Failed to create thread")

@app.get("/api/threads", response_model=List[ThreadResponse])
async def list_threads():
    return manager.list_threads()

@app.get("/api/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(thread_id: str):
    return manager.get_thread_history(thread_id)

@app.post("/api/threads/{thread_id}/messages", response_model=MessageResponse)
async def post_message(thread_id: str, msg: MessageCreate):
    try:
        response_text = manager.post_message(thread_id, msg.content)
        return {
            "role": "assistant",
            "content": response_text,
            "timestamp": "" # ThreadManager doesn't return TS but it's in DB
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status": "healthy", "version": "1.0.0"}
