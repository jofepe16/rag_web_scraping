from app.domain.models import PageDocument
from app.services.indexing import TextChunker


def test_chunker_produces_stable_overlapping_chunks():
    document = PageDocument(url="https://example.com", title="Test", text="Texto de prueba. " * 30)
    chunker = TextChunker(chunk_size=100, overlap=20)

    first = chunker.split(document)
    second = chunker.split(document)

    assert len(first) > 1
    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert all(len(chunk.text) <= 100 for chunk in first)

