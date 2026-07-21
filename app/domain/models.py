from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PageDocument:
    url: str
    title: str
    text: str
    fetched_at: datetime = field(default_factory=utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TextChunk:
    id: str
    url: str
    title: str
    text: str
    position: int


@dataclass(frozen=True)
class SearchResult:
    chunk: TextChunk
    score: float


@dataclass(frozen=True)
class ChatTurn:
    role: str
    content: str
    created_at: datetime = field(default_factory=utc_now)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    latency_ms: Optional[int] = None

