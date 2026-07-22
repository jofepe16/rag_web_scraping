from app.domain.models import SearchResult, TextChunk
from app.services.reranking import HybridLexicalReranker


def result(identifier: str, text: str, score: float) -> SearchResult:
    return SearchResult(TextChunk(identifier, "https://example.com", "Título", text, 0), score)


def test_reranker_promotes_lexically_relevant_result():
    results = [result("1", "contenido general", 0.8), result("2", "cuenta de ahorros sin cuota", 0.7)]

    ranked = HybridLexicalReranker().rerank("cuenta de ahorros", results, 2)

    assert ranked[0].chunk.id == "2"

