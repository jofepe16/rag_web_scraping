from dataclasses import dataclass

from app.config import Settings
from app.domain.ports import EmbeddingPort, GeneratorPort, VectorStorePort
from app.infrastructure.fastembed import FastEmbedEmbeddingAdapter
from app.infrastructure.ollama import OllamaGeneratorAdapter
from app.infrastructure.qdrant_store import QdrantVectorStore


@dataclass(frozen=True)
class AIProviders:
    embeddings: EmbeddingPort
    generator: GeneratorPort
    vectors: VectorStorePort


class ProviderFactory:
    """Centraliza la creación de los proveedores usados por la aplicación."""

    @staticmethod
    def create(settings: Settings) -> AIProviders:
        return AIProviders(
            embeddings=FastEmbedEmbeddingAdapter(
                settings.embedding_model, settings.fastembed_cache_path
            ),
            generator=OllamaGeneratorAdapter(settings.ollama_url, settings.chat_model),
            vectors=QdrantVectorStore(settings.qdrant_url, settings.qdrant_collection),
        )
