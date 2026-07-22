import pytest

from app.domain.models import ChatTurn
from app.infrastructure.database import SQLConversationRepository
from app.services.rag import RAGService
from app.services.reranking import HybridLexicalReranker
from tests.fakes import FakeEmbeddings, FakeGenerator, FakeVectorStore


@pytest.mark.asyncio
async def test_rag_answers_with_sources_and_persists_turns(tmp_path):
    repository = SQLConversationRepository(f"sqlite:///{tmp_path}/test.db")
    generator = FakeGenerator()
    service = RAGService(
        FakeEmbeddings(), generator, FakeVectorStore(), repository, HybridLexicalReranker(), 4, 5, 2
    )

    response = await service.ask("abc", "¿La cuenta tiene cuota?")

    assert response["answer"] == "Respuesta basada en [Fuente 1]."
    assert response["sources"][0]["url"] == "https://example.com"
    assert len(repository.recent_turns("abc", 10)) == 2
    assert "La cuenta no tiene cuota" in generator.prompt


@pytest.mark.asyncio
async def test_rag_uses_recent_history_for_follow_up_retrieval(tmp_path):
    repository = SQLConversationRepository(f"sqlite:///{tmp_path}/test.db")
    repository.add_turn("abc", ChatTurn(role="user", content="Háblame de la Cuenta Meta"))
    repository.add_turn("abc", ChatTurn(role="assistant", content="Ofrece 8,5% anual"))
    embeddings = FakeEmbeddings()
    service = RAGService(
        embeddings, FakeGenerator(), FakeVectorStore(), repository, HybridLexicalReranker(), 4, 5, 2
    )

    await service.ask("abc", "¿Cuál era el porcentaje?")

    assert "Cuenta Meta" in embeddings.texts[0]
    assert "¿Cuál era el porcentaje?" in embeddings.texts[0]
