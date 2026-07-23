import pytest

import app.services.scraper as scraper_module
from app.services.scraper import WebsiteScraper


class StoreStub:
    def save_raw(self, url, html):
        pass

    def save_clean(self, document):
        pass


def test_cleaner_removes_navigation_and_scripts():
    html = """<html><head><title>Banco</title><script>secret()</script></head>
    <body><nav>Menú global</nav><main><h1>Cuenta de ahorros</h1><p>Información útil para clientes.</p></main></body></html>"""

    document = WebsiteScraper._clean(html, "https://example.com")

    assert document.title == "Banco"
    assert "Información útil" in document.text
    assert "Menú global" not in document.text
    assert "secret" not in document.text


def test_scraper_stays_inside_domain_and_colombia_path():
    scraper = WebsiteScraper(StoreStub(), ["www.bbva.com"], "/es/co/", 10, 0, 10)

    assert scraper._is_allowed("https://www.bbva.com/es/co/economia/")
    assert not scraper._is_allowed("https://www.bbva.com/es/mx/economia/")
    assert not scraper._is_allowed("https://otro-banco.com/es/co/")


@pytest.mark.asyncio
async def test_scraper_uses_browser_compatible_session(monkeypatch):
    class ResponseStub:
        def __init__(self, url, text, content_type):
            self.url = url
            self.text = text
            self.headers = {"content-type": content_type}

        def raise_for_status(self):
            return None

    class SessionStub:
        def __init__(self, **kwargs):
            assert kwargs["impersonate"] == "chrome"

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, **kwargs):
            assert kwargs == {"timeout": 10, "allow_redirects": True}
            if url.endswith("robots.txt"):
                return ResponseStub(url, "User-agent: *\nAllow: /", "text/plain")
            html = "<html><head><title>BBVA</title></head><body><main>" + ("Contenido " * 20) + "</main></body></html>"
            return ResponseStub(url, html, "text/html; charset=UTF-8")

    class RecordingStore(StoreStub):
        def __init__(self):
            self.raw = []
            self.clean = []

        def save_raw(self, url, html):
            self.raw.append((url, html))

        def save_clean(self, document):
            self.clean.append(document)

    monkeypatch.setattr(scraper_module, "AsyncSession", SessionStub)
    store = RecordingStore()
    scraper = WebsiteScraper(store, ["www.bbva.com.co"], "/", 1, 0, 10)

    documents = await scraper.crawl("https://www.bbva.com.co/")

    assert len(documents) == 1
    assert len(store.raw) == 1
    assert store.clean[0].title == "BBVA"
