from __future__ import annotations

import asyncio

from typing import Dict, Any, List

# Your modules
from akinus.web.search.brave import async_brave_search

# ---- Optional async logger shim (so this file runs even if your logger changes) ----
try:
    from akinus.utils.logger import log as _alog   # async def
except Exception:
    async def _alog(level: str, where: str, msg: str) -> None:  # type: ignore
        print(f"{level} {where}: {msg}")

async def research_brave(query: str, limit: int = 5) -> list[dict]:
    from akinus.web.search.brave import async_brave_search
    limit = int(limit)
    results = await async_brave_search(query, count=limit)
    if not results:
        await _alog("WARNING", "research_brave.py", f"No URLs found for query='{query}'")
    
    return [
        {
            "title": r.get("title", ""),
            "url": r["url"],
            "source": "Brave",
            "snippet": r.get("snippet", ""),
            "date": r.get("date"),
            "authors": r.get("authors", []),
        }
        for r in results if r.get("url")
    ]

