from typing import List, Sequence

import httpx

from app.domain.ports import EmbeddingPort, GeneratorPort


class OllamaEmbeddingAdapter(EmbeddingPort):
    def __init__(self, base_url: str, model: str, timeout: float = 60) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embed", json={"model": self.model, "input": list(texts)}
            )
            response.raise_for_status()
            vectors = response.json().get("embeddings", [])
        if len(vectors) != len(texts):
            raise RuntimeError("Ollama returned an unexpected number of embeddings")
        return vectors


class OllamaGeneratorAdapter(GeneratorPort):
    def __init__(self, base_url: str, model: str, timeout: float = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "options": {"temperature": 0.1}},
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty response")
        return answer

