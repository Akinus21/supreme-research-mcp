from __future__ import annotations
import asyncio
import re
from urllib.parse import urlparse

import aiohttp

from akinus.utils.exceptions import ScrapeError

# Import all your extractors
from akinus.web.scrape.extract.beautiful_soup import beautiful_soup_extract
from akinus.web.scrape.extract.newspaper3k import newspaper3k_extract
from akinus.web.scrape.extract.readability import readability_extract
from akinus.web.scrape.extract.trafilatura import trafilatura_extract
from akinus.web.scrape.extract.pdf import pdf_extract


async def extract_from_url(url: str) -> str:
    """
    Unified extractor for PDFs and HTML.
    Fully async: uses aiohttp for fetch and threads for blocking parsers.
    """
    text_parts = []

    is_pdf = url.lower().endswith(".pdf")
    try:
        if is_pdf:
            # Run all PDF extractors in parallel
            pdf_tasks = [
                asyncio.create_task(pdf_extract(url))
            ]
            pdf_texts = await asyncio.gather(*pdf_tasks)
            for t in pdf_texts:
                if t:
                    text_parts.append(t)
        else:
            # Fetch HTML asynchronously
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status != 200:
                        raise ScrapeError(f"Failed to fetch HTML: status {resp.status}")
                    html = await resp.text()

            # Run all HTML extractors in parallel using threads for blocking calls
            tasks = [
                asyncio.to_thread(beautiful_soup_extract, type("Doc", (), {"html": html})()),
                asyncio.to_thread(newspaper3k_extract, url),
                asyncio.to_thread(readability_extract, type("Doc", (), {"html": html, "url": url})()),
                asyncio.to_thread(trafilatura_extract, type("Doc", (), {"html": html, "url": url})()),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    continue
                if r:
                    text_parts.append(r)

        combined_text = "\n\n".join(text_parts)
        if not combined_text:
            raise ScrapeError("No content extracted from URL")
        # Clean up whitespace
        combined_text = re.sub(r"\s+", " ", combined_text).strip()
        return combined_text

    except Exception as e:
        raise ScrapeError(f"Extraction failed for URL {url}: {e}") from e
