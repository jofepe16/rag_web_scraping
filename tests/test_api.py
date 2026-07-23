from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_rag_service, get_repository
from app.api.routes import router
from app.domain.models import ChatTurn
from app.infrastructure.database import SQLConversationRepository


class StubRAGService:
    async def ask(self, session_id: str, question: str) -> dict:
        return {
            "session_id": session_id,
            "answer": f"Respuesta para: {question}",
            "sources": [{"title": "Fuente", "url": "https://example.com", "score": 0.8}],
            "latency_ms": 25,
        }


def build_client(tmp_path) -> TestClient:
    repository = SQLConversationRepository(f"sqlite:///{tmp_path}/api.db")
    repository.add_turn("demo", ChatTurn(role="user", content="Pregunta"))
    repository.add_turn("demo", ChatTurn(role="assistant", content="Respuesta", sources=[]))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_rag_service] = lambda: StubRAGService()
    app.dependency_overrides[get_repository] = lambda: repository
    return TestClient(app)


def test_health_and_chat_routes(tmp_path):
    client = build_client(tmp_path)

    assert client.get("/api/v1/health").json() == {"status": "ok"}

    response = client.post(
        "/api/v1/chat",
        json={"session_id": "web_demo", "question": "¿Qué ofrece la cuenta?"},
    )

    assert response.status_code == 200
    assert response.json()["sources"][0]["url"] == "https://example.com"


def test_api_validates_session_and_reads_persisted_metrics(tmp_path):
    client = build_client(tmp_path)

    invalid = client.post(
        "/api/v1/chat",
        json={"session_id": "sesión no válida", "question": "Una pregunta"},
    )
    analytics = client.get("/api/v1/analytics")
    conversations = client.get("/api/v1/conversations")

    assert invalid.status_code == 422
    assert analytics.json()["answers_without_sources"] == 1
    assert conversations.json()["items"][0]["session_id"] == "demo"
