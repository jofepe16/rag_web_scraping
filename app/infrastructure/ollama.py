from typing import List, Sequence

from langchain_ollama import ChatOllama, OllamaEmbeddings

from app.domain.ports import EmbeddingPort, GeneratorPort


class OllamaEmbeddingAdapter(EmbeddingPort):
    def __init__(self, base_url: str, model: str, timeout: float = 60) -> None:
        self.client = OllamaEmbeddings(
            base_url=base_url.rstrip("/"), model=model, client_kwargs={"timeout": timeout}
        )

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = await self.client.aembed_documents(list(texts))
        if len(vectors) != len(texts):
            raise RuntimeError("Ollama returned an unexpected number of embeddings")
        return vectors


class OllamaGeneratorAdapter(GeneratorPort):
    def __init__(self, base_url: str, model: str, timeout: float = 600) -> None:
        self.client = ChatOllama(
            base_url=base_url.rstrip("/"),
            model=model,
            temperature=0.1,
            keep_alive="30m",
            client_kwargs={"timeout": timeout},
        )

    async def generate(self, prompt: str) -> str:
        response = await self.client.ainvoke(prompt)
        answer = response.content.strip() if isinstance(response.content, str) else ""
        if not answer:
            raise RuntimeError("Ollama returned an empty response")
        return answer
