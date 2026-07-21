from abc import ABC, abstractmethod
from typing import Iterable, List, Sequence

from app.domain.models import ChatTurn, PageDocument, SearchResult, TextChunk


class EmbeddingPort(ABC):
    @abstractmethod
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError


class GeneratorPort(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        raise NotImplementedError


class VectorStorePort(ABC):
    @abstractmethod
    async def index(self, chunks: Sequence[TextChunk], vectors: Sequence[Sequence[float]]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def search(self, vector: Sequence[float], limit: int) -> List[SearchResult]:
        raise NotImplementedError


class ConversationRepositoryPort(ABC):
    @abstractmethod
    def add_turn(self, session_id: str, turn: ChatTurn) -> None:
        raise NotImplementedError

    @abstractmethod
    def recent_turns(self, session_id: str, limit: int) -> List[ChatTurn]:
        raise NotImplementedError

    @abstractmethod
    def list_sessions(self, limit: int, offset: int) -> Iterable[dict]:
        raise NotImplementedError

    @abstractmethod
    def metrics(self) -> dict:
        raise NotImplementedError


class DocumentStorePort(ABC):
    @abstractmethod
    def save_raw(self, url: str, html: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def save_clean(self, document: PageDocument) -> None:
        raise NotImplementedError

