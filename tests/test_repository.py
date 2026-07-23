from app.domain.models import ChatTurn
from app.infrastructure.database import SQLConversationRepository


def test_repository_persists_history_and_metrics(tmp_path):
    repository = SQLConversationRepository(f"sqlite:///{tmp_path}/test.db")
    repository.add_turn("session-1", ChatTurn(role="user", content="Pregunta"))
    repository.add_turn(
        "session-1",
        ChatTurn(
            role="assistant",
            content="Respuesta",
            sources=[{"url": "https://example.com"}],
            latency_ms=120,
        ),
    )

    history = repository.recent_turns("session-1", 10)
    metrics = repository.metrics()

    assert [turn.role for turn in history] == ["user", "assistant"]
    assert metrics["total_sessions"] == 1
    assert metrics["total_questions"] == 1
    assert metrics["average_response_latency_ms"] == 120
    assert metrics["answers_with_sources"] == 1
    assert metrics["answers_without_sources"] == 0
    assert metrics["source_coverage_percentage"] == 100
