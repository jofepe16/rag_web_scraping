import uuid
from typing import Iterable, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.models import PageDocument, TextChunk
from app.domain.ports import EmbeddingPort, VectorStorePort


class TextChunker:
    """Divide una página limpia en fragmentos estables con solapamiento."""

    def __init__(self, chunk_size: int, overlap: int) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split(self, document: PageDocument) -> List[TextChunk]:
        contents = self.splitter.split_text(document.text.strip())
        return [TextChunk(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document.url}:{position}:{content}")),
            url=document.url,
            title=document.title,
            text=content,
            position=position,
        ) for position, content in enumerate(contents)]


class IndexingService:
    """Genera embeddings por lotes y los guarda en la base vectorial."""

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
