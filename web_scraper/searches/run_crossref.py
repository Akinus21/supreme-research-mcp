# research_crossref.py
from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from akinus.web.search.crossref import async_crossref_search

# Optional logger shim
try:
    from akinus.utils.logger import log as _alog
except Exception:
    async def _alog(level: str, where: str, msg: str) -> None:
        print(f"{level} {where}: {msg}")


async def research_crossref(query: str, limit: int = 3) -> list[dict]:
    from akinus.web.search.crossref import async_crossref_search

    results = await async_crossref_search(query, max_results=limit)
    if not results:
        await _alog("WARNING", "research_crossref.py", f"No results found for query='{query}'")
    
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url"),
            "source": "CrossRef",
            "snippet": r.get("abstract", ""),
            "date": r.get("published_date"),
            "authors": r.get("authors", []),
        }
        for r in results if r.get("url")
    ]

