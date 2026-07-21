from functools import lru_cache

from app.config import get_settings
from app.infrastructure.database import SQLConversationRepository
from app.infrastructure.factory import ProviderFactory
from app.infrastructure.file_store import LocalDocumentStore
from app.services.indexing import IndexingService, TextChunker
from app.services.rag import RAGService
from app.services.reranking import HybridLexicalReranker
from app.services.scraper import WebsiteScraper


@lru_cache
def get_repository() -> SQLConversationRepository:
    return SQLConversationRepository(get_settings().database_url)


@lru_cache
def get_rag_service() -> RAGService:
    settings = get_settings()
    providers = ProviderFactory.create(settings)
    return RAGService(
        embeddings=providers.embeddings,
        generator=providers.generator,
        vectors=providers.vectors,
        conversations=get_repository(),
        reranker=HybridLexicalReranker(),
        history_window=settings.history_window,
        retrieval_top_k=settings.retrieval_top_k,
        rerank_top_k=settings.rerank_top_k,
    )


def get_ingestion_services():
    settings = get_settings()
    providers = ProviderFactory.create(settings)
    scraper = WebsiteScraper(
        store=LocalDocumentStore(), allowed_domains=settings.allowed_domains,
        max_pages=settings.scrape_max_pages, delay_seconds=settings.scrape_delay_seconds,
        timeout_seconds=settings.request_timeout_seconds,
    )
    indexer = IndexingService(
        TextChunker(settings.chunk_size, settings.chunk_overlap), providers.embeddings, providers.vectors
    )
    return scraper, indexer

