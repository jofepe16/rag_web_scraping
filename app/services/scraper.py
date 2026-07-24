import asyncio
import logging
import xml.etree.ElementTree as ET
from collections import deque
from typing import List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from curl_cffi.requests.errors import RequestsError

from app.domain.models import PageDocument
from app.domain.ports import DocumentStorePort

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Recorre un número limitado de páginas y guarda su contenido."""

    SKIPPED_SUFFIXES = (
        ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".mp3", ".mp4",
        ".wav", ".m4a", ".ogg", ".webm", ".avi", ".mov", ".doc", ".docx", ".xls",
        ".xlsx", ".ppt", ".pptx", ".xml",
    )

    def __init__(self, store: DocumentStorePort, allowed_domains: List[str], allowed_path_prefix: str,
                 max_pages: int, delay_seconds: float, timeout_seconds: float,
                 concurrency: int = 3) -> None:
        self.store = store
        self.allowed_domains = set(allowed_domains)
        self.allowed_path_prefix = allowed_path_prefix.rstrip("/") + "/"
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds
        self.concurrency = concurrency

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.lower() in self.allowed_domains
            and parsed.path.startswith(self.allowed_path_prefix)
            and not parsed.path.lower().endswith(self.SKIPPED_SUFFIXES)
        )

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Elimina fragmentos y parámetros usados para seguimiento."""
        parsed = urlparse(url)
        return parsed._replace(query="", fragment="").geturl()

    @staticmethod
    def _clean(html: str, url: str) -> PageDocument:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select("script, style, noscript, svg, nav, footer, header, form, aside"):
            node.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else url
        root = soup.select_one("main, article, [role='main']") or soup.body or soup
        lines = [" ".join(line.split()) for line in root.get_text("\n").splitlines()]
        text = "\n".join(dict.fromkeys(line for line in lines if len(line) > 2))
        return PageDocument(url=url, title=title, text=text, metadata={"content_length": len(text)})

    async def _sitemap_urls(self, client: AsyncSession, sitemap_urls: List[str]) -> List[str]:
        """Obtiene las páginas declaradas en sitemaps e índices de sitemaps."""
        pending = deque(url for url in sitemap_urls if "image" not in url.lower())
        visited_sitemaps: Set[str] = set()
        discovered = []
        discovered_set: Set[str] = set()

        while pending:
            sitemap_url = pending.popleft()
            if sitemap_url in visited_sitemaps:
                continue
            visited_sitemaps.add(sitemap_url)
            try:
                response = await client.get(
                    sitemap_url, timeout=self.timeout_seconds, allow_redirects=True
                )
                response.raise_for_status()
                root = ET.fromstring(response.content)
            except (RequestsError, ET.ParseError) as exc:
                logger.warning("No se pudo leer el sitemap %s: %s", sitemap_url, exc)
                continue

            locations = [
                node.text.strip()
                for node in root.iter()
                if node.tag.endswith("loc") and node.text
            ]
            if root.tag.endswith("sitemapindex"):
                pending.extend(locations)
                continue
            for url in locations:
                if url not in discovered_set and self._is_allowed(url):
                    discovered_set.add(url)
                    discovered.append(self._normalize_url(url))
        return discovered

    async def _fetch_page(
        self, client: AsyncSession, url: str
    ) -> Tuple[Optional[PageDocument], List[str]]:
        """Descarga y limpia una página, y devuelve sus enlaces internos."""
        try:
            response = await client.get(
                url, timeout=self.timeout_seconds, allow_redirects=True
            )
            response.raise_for_status()
            if "text/html" not in response.headers.get("content-type", ""):
                return None, []
            self.store.save_raw(url, response.text)
            document = self._clean(response.text, str(response.url))
            if len(document.text) < 100:
                document = None
            else:
                self.store.save_clean(document)
            soup = BeautifulSoup(response.text, "html.parser")
            links = []
            for anchor in soup.select("a[href]"):
                candidate = self._normalize_url(
                    urljoin(str(response.url), anchor.get("href", ""))
                )
                if self._is_allowed(candidate):
                    links.append(candidate)
            return document, links
        except (RequestsError, OSError) as exc:
            logger.warning("No se pudo extraer %s: %s", url, exc)
            return None, []
        finally:
            if self.delay_seconds:
                await asyncio.sleep(self.delay_seconds)

    async def crawl(self, start_url: str) -> List[PageDocument]:
        queue = deque([start_url])
        visited: Set[str] = set()
        documents: List[PageDocument] = []
        robots_user_agent = "BBVAContentIndexer"
        async with AsyncSession(impersonate="chrome") as client:
            robots = RobotFileParser()
            robots_url = urljoin(start_url, "/robots.txt")
            try:
                robots_response = await client.get(
                    robots_url, timeout=self.timeout_seconds, allow_redirects=True
                )
                robots_response.raise_for_status()
                robots.set_url(robots_url)
                robots.parse(robots_response.text.splitlines())
            except RequestsError as exc:
                logger.warning("No se pudo leer robots.txt; continúa el recorrido limitado: %s", exc)
                robots = None
            if robots is not None:
                sitemap_pages = await self._sitemap_urls(client, robots.site_maps() or [])
                queue = deque(dict.fromkeys([start_url, *sitemap_pages]))
            while queue and len(visited) < self.max_pages:
                batch = []
                while (
                    queue and len(batch) < self.concurrency
                    and len(visited) < self.max_pages
                ):
                    url = self._normalize_url(queue.popleft())
                    if url in visited or not self._is_allowed(url):
                        continue
                    if robots is not None and not robots.can_fetch(robots_user_agent, url):
                        logger.info("robots.txt no permite consultar %s", url)
                        visited.add(url)
                        continue
                    visited.add(url)
                    batch.append(url)
                if not batch:
                    continue
                pages = await asyncio.gather(
                    *(self._fetch_page(client, url) for url in batch)
                )
                for document, links in pages:
                    if document is not None:
                        documents.append(document)
                        if len(documents) % 25 == 0:
                            logger.info(
                                "Progreso de scraping: %s páginas guardadas de un máximo de %s",
                                len(documents), self.max_pages,
                            )
                    for candidate in links:
                        if candidate not in visited:
                            queue.append(candidate)
        return documents
