from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    question: str = Field(min_length=2, max_length=2000)


class SourceResponse(BaseModel):
    title: str
    url: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: List[SourceResponse]
    latency_ms: int


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
    sources: List[dict]
    latency_ms: Optional[int] = None


class IngestionResponse(BaseModel):
    pages_scraped: int
    chunks_indexed: int

