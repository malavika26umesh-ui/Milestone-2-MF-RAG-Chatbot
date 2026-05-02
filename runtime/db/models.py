from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

class ChatThread(Base):
    __tablename__ = "threads"
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    messages = relationship("ChatMessage", back_populates="thread", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    thread_id = Column(String, ForeignKey("threads.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    thread = relationship("ChatThread", back_populates="messages")

class FundDocument(Base):
    """Stores the 'Ground Truth' normalized content for RAG retrieval."""
    __tablename__ = "fund_documents"
    scheme_id = Column(String, primary_key=True)
    scheme_name = Column(String)
    source_url = Column(String)
    content = Column(Text) # Normalized full text
    metadata_json = Column(JSON) # Store parsed facts, NAV, etc.
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Database Engine Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/threads.db")
# For Postgres on Render, we might need to handle the 'postgres://' vs 'postgresql://' issue
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
