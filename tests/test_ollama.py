import pytest
import respx
from httpx import Response

from app.infrastructure.ollama import OllamaEmbeddingAdapter


@pytest.mark.asyncio
@respx.mock
async def test_embedding_adapter_sends_one_text_per_request():
    route = respx.post("http://ollama:11434/api/embed").mock(
        side_effect=[Response(200, json={"embeddings": [[1.0, 0.0]]}),
                     Response(200, json={"embeddings": [[0.0, 1.0]]})]
    )
    adapter = OllamaEmbeddingAdapter("http://ollama:11434", "nomic-embed-text")

    vectors = await adapter.embed(["primer texto", "segundo texto"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert route.call_count == 2
