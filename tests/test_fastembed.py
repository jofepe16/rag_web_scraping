import pytest

import app.infrastructure.fastembed as fastembed_module
from app.infrastructure.fastembed import FastEmbedEmbeddingAdapter


@pytest.mark.asyncio
async def test_fastembed_adapter_returns_plain_vectors(monkeypatch, tmp_path):
    class VectorStub:
        def __init__(self, values):
            self.values = values

        def tolist(self):
            return self.values

    class TextEmbeddingStub:
        def __init__(self, **kwargs):
            assert kwargs["model_name"] == "modelo-local"

        def embed(self, texts, batch_size):
            assert batch_size == 32
            return [VectorStub([float(len(text)), 1.0]) for text in texts]

    monkeypatch.setattr(fastembed_module, "TextEmbedding", TextEmbeddingStub)
    adapter = FastEmbedEmbeddingAdapter("modelo-local", str(tmp_path / "models"))

    vectors = await adapter.embed(["uno", "cuatro"])

    assert vectors == [[3.0, 1.0], [6.0, 1.0]]
