from typing import List, Sequence

from qdrant_client import AsyncQdrantClient, models

from app.domain.models import SearchResult, TextChunk
from app.domain.ports import VectorStorePort


class QdrantVectorStore(VectorStorePort):
    """Guarda y consulta fragmentos vectorizados en Qdrant."""

    def __init__(self, url: str, collection: str) -> None:
        self.client = AsyncQdrantClient(url=url)
        self.collection = collection

    async def _ensure_collection(self, vector_size: int) -> None:
        if not await self.client.collection_exists(self.collection):
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )

    async def index(self, chunks: Sequence[TextChunk], vectors: Sequence[Sequence[float]]) -> int:
        if not chunks:
            return 0
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        await self._ensure_collection(len(vectors[0]))
        points = [models.PointStruct(
            id=chunk.id,
            vector=list(vector),
            payload={"url": chunk.url, "title": chunk.title, "text": chunk.text, "position": chunk.position},
        ) for chunk, vector in zip(chunks, vectors)]
        await self.client.upsert(collection_name=self.collection, points=points, wait=True)
        return len(points)

    async def search(self, vector: Sequence[float], limit: int) -> List[SearchResult]:
        if not await self.client.collection_exists(self.collection):
            return []
        response = await self.client.query_points(
            collection_name=self.collection, query=list(vector), limit=limit, with_payload=True
        )
        results = []
        for point in response.points:
            payload = point.payload or {}
            results.append(SearchResult(
                chunk=TextChunk(
                    id=str(point.id), url=str(payload.get("url", "")), title=str(payload.get("title", "")),
                    text=str(payload.get("text", "")), position=int(payload.get("position", 0)),
                ), score=float(point.score),
            ))
        return results
