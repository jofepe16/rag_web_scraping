import re
import uuid
from typing import Iterable, List

from app.domain.models import PageDocument, TextChunk
from app.domain.ports import EmbeddingPort, VectorStorePort


class TextChunker:
    def __init__(self, chunk_size: int, overlap: int) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, document: PageDocument) -> List[TextChunk]:
        text = re.sub(r"\n{3,}", "\n\n", document.text).strip()
        chunks: List[TextChunk] = []
        start = 0
        position = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
                if boundary > start + self.chunk_size // 2:
                    end = boundary + 1
            content = text[start:end].strip()
            if content:
                key = f"{document.url}:{position}:{content}"
                chunks.append(TextChunk(
                    id=str(uuid.uuid5(uuid.NAMESPACE_URL, key)), url=document.url,
                    title=document.title, text=content, position=position,
                ))
                position += 1
            if end >= len(text):
                break
            start = max(start + 1, end - self.overlap)
        return chunks


class IndexingService:
    def __init__(self, chunker: TextChunker, embeddings: EmbeddingPort, vectors: VectorStorePort,
                 batch_size: int = 32) -> None:
        self.chunker = chunker
        self.embeddings = embeddings
        self.vectors = vectors
        self.batch_size = batch_size

    async def index(self, documents: Iterable[PageDocument]) -> int:
        chunks = [chunk for document in documents for chunk in self.chunker.split(document)]
        indexed = 0
        for start in range(0, len(chunks), self.batch_size):
            batch = chunks[start:start + self.batch_size]
            vectors = await self.embeddings.embed([chunk.text for chunk in batch])
            indexed += await self.vectors.index(batch, vectors)
        return indexed

