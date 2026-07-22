import asyncio
import logging
from collections import deque
from typing import List, Set
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from app.domain.models import PageDocument
from app.domain.ports import DocumentStorePort

logger = logging.getLogger(__name__)


class WebsiteScraper:
    """Bounded, same-domain crawler that persists both raw and clean content."""

    SKIPPED_SUFFIXES = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip", ".mp4", ".xml")

    def __init__(self, store: DocumentStorePort, allowed_domains: List[str], max_pages: int,
                 delay_seconds: float, timeout_seconds: float) -> None:
        self.store = store
        self.allowed_domains = set(allowed_domains)
        self.max_pages = max_pages
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds

    def _is_allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        return (
            parsed.scheme in {"http", "https"}
            and parsed.netloc.lower() in self.allowed_domains
            and not parsed.path.lower().endswith(self.SKIPPED_SUFFIXES)
        )

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

    async def crawl(self, start_url: str) -> List[PageDocument]:
        queue = deque([start_url])
        visited: Set[str] = set()
        documents: List[PageDocument] = []
        headers = {"User-Agent": "InetumMLEChallengeBot/1.0 (educational project)"}
        async with httpx.AsyncClient(headers=headers, timeout=self.timeout_seconds, follow_redirects=True) as client:
            robots = RobotFileParser()
            robots_url = urljoin(start_url, "/robots.txt")
            try:
                robots_response = await client.get(robots_url)
                robots_response.raise_for_status()
                robots.set_url(robots_url)
                robots.parse(robots_response.text.splitlines())
            except httpx.HTTPError as exc:
                logger.warning("Could not read robots.txt; continuing with the bounded crawler: %s", exc)
                robots = None
            while queue and len(visited) < self.max_pages:
                url = queue.popleft()
                url, _ = urldefrag(url)
                if url in visited or not self._is_allowed(url):
                    continue
                if robots is not None and not robots.can_fetch(headers["User-Agent"], url):
                    logger.info("robots.txt disallows %s", url)
                    visited.add(url)
                    continue
                visited.add(url)
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    if "text/html" not in response.headers.get("content-type", ""):
                        continue
                    self.store.save_raw(url, response.text)
                    document = self._clean(response.text, str(response.url))
                    if len(document.text) >= 100:
                        self.store.save_clean(document)
                        documents.append(document)
                    soup = BeautifulSoup(response.text, "html.parser")
                    for anchor in soup.select("a[href]"):
                        candidate, _ = urldefrag(urljoin(str(response.url), anchor.get("href", "")))
                        if candidate not in visited and self._is_allowed(candidate):
                            queue.append(candidate)
                except (httpx.HTTPError, OSError) as exc:
                    logger.warning("Could not scrape %s: %s", url, exc)
                if self.delay_seconds:
                    await asyncio.sleep(self.delay_seconds)
        return documents
