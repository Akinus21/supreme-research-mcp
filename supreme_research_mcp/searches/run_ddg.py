# research_duckduckgo.py
from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from akinus.web.search.duckduckgo import async_duckduckgo_search

# Optional logger shim
try:
    from akinus.utils.logger import log as _alog
except Exception:
    async def _alog(level: str, where: str, msg: str) -> None:
        print(f"{level} {where}: {msg}")


async def research_duckduckgo(query: str, limit: int = 3) -> list[dict]:
    results = await async_duckduckgo_search(query, max_results=limit)
    urls = [r for r in results if r.get("url")]

    if not urls:
        await _alog("WARNING", "research_duckduckgo.py", f"No URLs found for query='{query}'")

    return [
        {
            "title": r.get("title", ""),
            "url": r["url"],
            "source": "DuckDuckGo",
            "snippet": r.get("snippet", ""),
            "date": r.get("date"),
            "authors": r.get("authors", []),
        }
        for r in urls
    ]
