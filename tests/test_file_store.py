import json

from app.domain.models import PageDocument
from app.infrastructure.file_store import LocalDocumentStore


def test_file_store_separates_raw_and_clean_content(tmp_path):
    raw_dir = tmp_path / "raw"
    clean_dir = tmp_path / "clean"
    store = LocalDocumentStore(str(raw_dir), str(clean_dir))
    document = PageDocument(
        url="https://example.com/cuenta",
        title="Cuenta de ahorro",
        text="Contenido normalizado",
    )

    store.save_raw(document.url, "<html>Contenido original</html>")
    store.save_clean(document)

    raw_file = next(raw_dir.glob("*.html"))
    clean_file = next(clean_dir.glob("*.json"))
    clean_payload = json.loads(clean_file.read_text(encoding="utf-8"))

    assert "Contenido original" in raw_file.read_text(encoding="utf-8")
    assert clean_payload["text"] == "Contenido normalizado"
    assert raw_file.stem == clean_file.stem
