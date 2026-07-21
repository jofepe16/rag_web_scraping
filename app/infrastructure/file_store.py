import hashlib
import json
from pathlib import Path

from app.domain.models import PageDocument
from app.domain.ports import DocumentStorePort


class LocalDocumentStore(DocumentStorePort):
    """Stores immutable raw HTML and normalized JSON as separate artifacts."""

    def __init__(self, raw_dir: str = "data/raw", clean_dir: str = "data/clean") -> None:
        self.raw_dir = Path(raw_dir)
        self.clean_dir = Path(clean_dir)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.clean_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]

    def save_raw(self, url: str, html: str) -> None:
        self.raw_dir.joinpath(f"{self._key(url)}.html").write_text(html, encoding="utf-8")

    def save_clean(self, document: PageDocument) -> None:
        payload = {
            "url": document.url,
            "title": document.title,
            "text": document.text,
            "fetched_at": document.fetched_at.isoformat(),
            "metadata": document.metadata,
        }
        self.clean_dir.joinpath(f"{self._key(document.url)}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

