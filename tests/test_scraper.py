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
