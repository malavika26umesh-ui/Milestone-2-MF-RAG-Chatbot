import uuid
import json
from datetime import datetime
from typing import List, Dict, Optional
from runtime.phase_8_threads.models import get_connection, init_db
from runtime.phase_7_safety.safety_manager import SafetyManager

class ThreadManager:
    def __init__(self, max_turns: int = 5):
        init_db()
        self.safety_manager = SafetyManager()
        self.max_turns = max_turns

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        thread_id = str(uuid.uuid4())
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO threads (id, metadata) VALUES (?, ?)",
            (thread_id, json.dumps(metadata) if metadata else None)
        )
        conn.commit()
        conn.close()
        return thread_id

    def list_threads(self) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, created_at FROM threads ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [{"id": r[0], "created_at": r[1]} for r in rows]

    def get_thread_history(self, thread_id: str, limit: int = 10) -> List[Dict]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE thread_id = ? ORDER BY timestamp DESC LIMIT ?",
            (thread_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        # Return in chronological order
        return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in reversed(rows)]

    def post_message(self, thread_id: str, content: str) -> str:
        """
        Processes a user message within a thread and returns the assistant's response.
        """
        # 1. Store user message
        self._save_message(thread_id, "user", content)
        
        # 2. Get recent history for context window (§229)
        history = self.get_thread_history(thread_id, limit=self.max_turns * 2)
        
        # 3. Query Expansion / Contextualization (§230)
        # If there's history, we might need to clarify the query (e.g., "What about its NAV?")
        processed_query = self._expand_query(content, history)
        
        # 4. Get response from Safety Layer (Phase 7 -> 5 -> 6)
        response = self.safety_manager.answer(processed_query)
        
        # 5. Store assistant message
        self._save_message(thread_id, "assistant", response)
        
        return response

    def _save_message(self, thread_id: str, role: str, content: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)",
            (thread_id, role, content)
        )
        conn.commit()
        conn.close()

    def _expand_query(self, query: str, history: List[Dict]) -> str:
        """
        Simple heuristic: if history is present and query is short/vague, 
        prepend context from previous turns.
        In a full implementation, this could be another LLM call.
        """
        if len(history) <= 1: # Only current user message
            return query
            
        # For now, we'll use a simple heuristic: 
        # If the user says "it", "its", "this", or "that", try to find a fund name in history.
        # However, to be more robust, we'll just return the original query for now,
        # but the infrastructure is here for LLM-based expansion.
        return query
