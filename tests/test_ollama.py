import pytest
import respx
from httpx import Response

from app.infrastructure.ollama import OllamaEmbeddingAdapter, OllamaGeneratorAdapter


@pytest.mark.asyncio
@respx.mock
async def test_embedding_adapter_sends_texts_in_one_batch():
    route = respx.post("http://ollama:11434/api/embed").mock(
        return_value=Response(200, json={"embeddings": [[1.0, 0.0], [0.0, 1.0]]})
    )
    adapter = OllamaEmbeddingAdapter("http://ollama:11434", "nomic-embed-text")

    vectors = await adapter.embed(["primer texto", "segundo texto"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_generator_adapter_uses_langchain_chat_model():
    route = respx.post("http://ollama:11434/api/chat").mock(
        return_value=Response(200, json={
            "model": "llama3.2:1b",
            "message": {"role": "assistant", "content": "Respuesta local"},
            "done": True,
        })
    )
    adapter = OllamaGeneratorAdapter("http://ollama:11434", "llama3.2:1b")

    answer = await adapter.generate("Pregunta de prueba")

    assert answer == "Respuesta local"
    assert route.call_count == 1
