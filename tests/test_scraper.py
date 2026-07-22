from app.services.scraper import WebsiteScraper


def test_cleaner_removes_navigation_and_scripts():
    html = """<html><head><title>Banco</title><script>secret()</script></head>
    <body><nav>Menú global</nav><main><h1>Cuenta de ahorros</h1><p>Información útil para clientes.</p></main></body></html>"""

    document = WebsiteScraper._clean(html, "https://example.com")

    assert document.title == "Banco"
    assert "Información útil" in document.text
    assert "Menú global" not in document.text
    assert "secret" not in document.text

