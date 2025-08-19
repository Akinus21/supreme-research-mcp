# run_core.py
from __future__ import annotations

import asyncio
from typing import Dict, Any, List
from akinus.web.search.core import async_core_search

# Optional logger shim
try:
    from akinus.utils.logger import log as _alog
except Exception:
    async def _alog(level: str, where: str, msg: str) -> None:
        print(f"{level} {where}: {msg}")


async def research_core(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search CORE API and return clean metadata (no scraping).

    Each result will conform to the standard schema used across all search runners:
    {
        "title": str,
        "url": str,
        "abstract": str | None,
        "authors": List[str],
        "year": int | None,
        "source": "Core",
        "raw": dict   # original API response
    }
    """
    try:
        results = await async_core_search(query, max_results=limit)
    except Exception as e:
        await _alog("ERROR", "research_core.py", f"CORE search failed: {e}")
        return []

    if not results:
        await _alog("WARNING", "research_core.py", f"No results for query='{query}'")
        return []

    stitched: List[Dict[str, Any]] = []
    for r in results:
        stitched.append({
            "title": r.get("title"),
            "url": r.get("url"),
            "abstract": r.get("abstract"),
            "authors": r.get("authors", []),
            "year": r.get("year"),
            "source": "Core",
            "raw": r,   # keep full original API response for debugging/expansion
        })

    return stitched
