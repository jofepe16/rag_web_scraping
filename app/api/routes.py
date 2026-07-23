import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ollama import RequestError, ResponseError

from app.api.dependencies import get_ingestion_services, get_rag_service, get_repository
from app.api.schemas import ChatRequest, ChatResponse, IngestionResponse, MessageResponse
from app.config import get_settings
from app.infrastructure.database import SQLConversationRepository
from app.services.rag import RAGService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, service: RAGService = Depends(get_rag_service)) -> dict:
    try:
        return await service.ask(payload.session_id, payload.question.strip())
    except (httpx.ConnectError, RequestError) as exc:
        logger.exception("No fue posible conectar con Ollama o Qdrant")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="El servicio de IA no está disponible. Verifica Ollama y Qdrant.") from exc
    except httpx.TimeoutException as exc:
        logger.exception("Se agotó el tiempo de espera de una dependencia")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                            detail="El modelo tardó demasiado en responder. Intenta nuevamente.") from exc
    except (httpx.HTTPStatusError, ResponseError) as exc:
        logger.exception("Una dependencia respondió con error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Un servicio de IA respondió con error.") from exc
    except Exception as exc:
        logger.exception("Falló el procesamiento de la pregunta")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="No fue posible procesar la pregunta.") from exc


@router.get("/conversations")
def conversations(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                  repository: SQLConversationRepository = Depends(get_repository)) -> dict:
    return {"items": list(repository.list_sessions(limit, offset)), "limit": limit, "offset": offset}


@router.get("/conversations/{session_id}", response_model=list[MessageResponse])
def conversation_history(session_id: str, limit: int = Query(100, ge=1, le=500),
                         repository: SQLConversationRepository = Depends(get_repository)):
    return repository.recent_turns(session_id, limit)


@router.get("/analytics")
def analytics(repository: SQLConversationRepository = Depends(get_repository)) -> dict:
    return repository.metrics()


@router.post("/ingestion", response_model=IngestionResponse)
async def ingest() -> dict:
    settings = get_settings()
    scraper, indexer = get_ingestion_services()
    try:
        documents = await scraper.crawl(settings.scrape_base_url)
        indexed = await indexer.index(documents)
        return {"pages_scraped": len(documents), "chunks_indexed": indexed}
    except httpx.HTTPError as exc:
        logger.exception("Falló una dependencia durante la ingesta")
        raise HTTPException(status_code=502, detail="Falló una dependencia durante la ingesta.") from exc
    except Exception as exc:
        logger.exception("Falló la ingesta")
        raise HTTPException(status_code=500, detail="No fue posible completar la ingesta.") from exc
