from dataclasses import dataclass

from app.config import Settings
from app.domain.ports import EmbeddingPort, GeneratorPort, VectorStorePort
from app.infrastructure.ollama import OllamaEmbeddingAdapter, OllamaGeneratorAdapter
from app.infrastructure.qdrant_store import QdrantVectorStore


@dataclass(frozen=True)
class AIProviders:
    embeddings: EmbeddingPort
    generator: GeneratorPort
    vectors: VectorStorePort


class ProviderFactory:
    """Factory pattern: centralizes construction of replaceable AI providers."""

    @staticmethod
    def create(settings: Settings) -> AIProviders:
        return AIProviders(
            embeddings=OllamaEmbeddingAdapter(settings.ollama_url, settings.embedding_model),
            generator=OllamaGeneratorAdapter(settings.ollama_url, settings.chat_model),
            vectors=QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection),
        )

