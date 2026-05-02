import uuid
from typing import List, Dict, Optional
from runtime.db.models import SessionLocal, ChatThread, ChatMessage, init_db
from runtime.phase_7_safety.safety_manager import SafetyManager

class ThreadManager:
    def __init__(self, max_turns: int = 5):
        init_db()
        self.safety_manager = SafetyManager()
        self.max_turns = max_turns

    def create_thread(self, metadata: Optional[Dict] = None) -> str:
        thread_id = str(uuid.uuid4())
        session = SessionLocal()
        try:
            new_thread = ChatThread(id=thread_id)
            session.add(new_thread)
            session.commit()
            return thread_id
        finally:
            session.close()

    def list_threads(self) -> List[Dict]:
        session = SessionLocal()
        try:
            threads = session.query(ChatThread).order_by(ChatThread.created_at.desc()).all()
            return [{"id": t.id, "created_at": t.created_at.isoformat() if t.created_at else None} for t in threads]
        finally:
            session.close()

    def get_thread_history(self, thread_id: str, limit: int = 10) -> List[Dict]:
        session = SessionLocal()
        try:
            messages = (
                session.query(ChatMessage)
                .filter(ChatMessage.thread_id == thread_id)
                .order_by(ChatMessage.timestamp.desc())
                .limit(limit)
                .all()
            )
            # Return in chronological order
            return [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat() if m.timestamp else None}
                for m in reversed(messages)
            ]
        finally:
            session.close()

    def post_message(self, thread_id: str, content: str) -> str:
        """
        Processes a user message within a thread and returns the assistant's response.
        """
        # 1. Store user message
        self._save_message(thread_id, "user", content)
        
        # 2. Get recent history for context window
        history = self.get_thread_history(thread_id, limit=self.max_turns * 2)
        
        # 3. Query Expansion / Contextualization
        processed_query = self._expand_query(content, history)
        
        # 4. Get response from Safety Layer
        response = self.safety_manager.answer(processed_query)
        
        # 5. Store assistant message
        self._save_message(thread_id, "assistant", response)
        
        return response

    def _save_message(self, thread_id: str, role: str, content: str):
        session = SessionLocal()
        try:
            msg_id = str(uuid.uuid4())
            new_msg = ChatMessage(id=msg_id, thread_id=thread_id, role=role, content=content)
            session.add(new_msg)
            session.commit()
        finally:
            session.close()

    def _expand_query(self, query: str, history: List[Dict]) -> str:
        # Placeholder for future LLM-based query expansion
        return query
