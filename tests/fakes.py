from typing import List, Sequence

from app.domain.models import SearchResult, TextChunk
from app.domain.ports import EmbeddingPort, GeneratorPort, VectorStorePort


class FakeEmbeddings(EmbeddingPort):
    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [[float(len(text)), 1.0] for text in texts]


class FakeGenerator(GeneratorPort):
    def __init__(self) -> None:
        self.prompt = ""

    async def generate(self, prompt: str) -> str:
        self.prompt = prompt
        return "Respuesta basada en [Fuente 1]."


class FakeVectorStore(VectorStorePort):
    def __init__(self) -> None:
        self.items = []

    async def index(self, chunks, vectors) -> int:
        self.items.extend(zip(chunks, vectors))
        return len(chunks)

    async def search(self, vector, limit: int):
        return [SearchResult(
            chunk=TextChunk(id="1", url="https://example.com", title="Cuenta", text="La cuenta no tiene cuota.", position=0),
            score=0.8,
        )]

