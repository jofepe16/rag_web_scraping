import re
from abc import ABC, abstractmethod
from typing import List, Sequence, Set

from app.domain.models import SearchResult


class RerankerStrategy(ABC):
    """Strategy pattern contract for interchangeable reranking algorithms."""

    @abstractmethod
    def rerank(self, query: str, results: Sequence[SearchResult], limit: int) -> List[SearchResult]:
        raise NotImplementedError


class HybridLexicalReranker(RerankerStrategy):
    """Combines vector similarity with token overlap without another paid model."""

    @staticmethod
    def _tokens(text: str) -> Set[str]:
        return {token for token in re.findall(r"[a-záéíóúñ0-9]+", text.lower()) if len(token) > 2}

    def rerank(self, query: str, results: Sequence[SearchResult], limit: int) -> List[SearchResult]:
        query_tokens = self._tokens(query)
        rescored = []
        for result in results:
            document_tokens = self._tokens(f"{result.chunk.title} {result.chunk.text}")
            lexical = len(query_tokens & document_tokens) / max(len(query_tokens), 1)
            score = (0.7 * result.score) + (0.3 * lexical)
            rescored.append(SearchResult(chunk=result.chunk, score=score))
        return sorted(rescored, key=lambda item: item.score, reverse=True)[:limit]

