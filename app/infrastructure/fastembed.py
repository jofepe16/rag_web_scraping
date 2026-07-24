import asyncio
import warnings
from pathlib import Path
from typing import List, Sequence

from fastembed import TextEmbedding

from app.domain.ports import EmbeddingPort


class FastEmbedEmbeddingAdapter(EmbeddingPort):
    """Genera embeddings locales optimizados para CPU mediante ONNX."""

    def __init__(self, model: str, cache_dir: str) -> None:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The model .* now uses mean pooling.*")
            self.client = TextEmbedding(model_name=model, cache_dir=cache_dir)

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []

        def encode() -> List[List[float]]:
            return [vector.tolist() for vector in self.client.embed(list(texts), batch_size=32)]

        return await asyncio.to_thread(encode)
