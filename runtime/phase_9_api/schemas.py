from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class ThreadResponse(BaseModel):
    id: str
    created_at: str

class HealthResponse(BaseModel):
    status: str
    version: str
