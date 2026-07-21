import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Asistente RAG sobre contenido institucional bancario.",
)
app.include_router(router)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def web_interface() -> FileResponse:
    return FileResponse(static_dir / "index.html")

