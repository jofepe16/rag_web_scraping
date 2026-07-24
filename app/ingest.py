import asyncio
import logging

from app.api.dependencies import get_ingestion_services
from app.config import get_settings


async def run() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    scraper, indexer = get_ingestion_services()
    documents = await scraper.crawl(settings.scrape_base_url)
    indexed = await indexer.index(documents)
    print(f"Ingesta terminada: {len(documents)} páginas, {indexed} fragmentos indexados.")


if __name__ == "__main__":
    asyncio.run(run())
