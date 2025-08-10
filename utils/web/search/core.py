import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import httpx
from utils.logger import local as log
import re
from utils.app_details import PROJECT_ROOT


# Load environment variables from .env file in the project root
env_file = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    raise FileNotFoundError(f"Environment file not found: {env_file}")

CORE_API_KEY = os.getenv("CORE_API_KEY")

# --------------------
# CORE API Search (async)
# --------------------
async def core_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    if not CORE_API_KEY:
        await log("ERROR", "search.py", "CORE_API_KEY not set in environment.")
        return []

    url = "https://api.core.ac.uk/v3/search/works/"  # <-- add trailing slash here
    headers = {"Authorization": f"Bearer {CORE_API_KEY}"}
    params = {
        "q": query,
        "page": 1,
        "pageSize": max_results
    }
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, headers=headers, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            results = []
            for item in data.get("results", []):
                authors = item.get("authors", [])
                results.append({
                    "title": item.get("title"),
                    "authors": authors,
                    "year": item.get("year"),
                    "journal": item.get("sourceTitle"),
                    "doi": item.get("doi"),
                    "url": item.get("downloadUrl") or item.get("url"),
                    "abstract": item.get("abstract"),
                })
            return results
        except Exception as e:
            await log("ERROR", "search.py", f"core_search failed: {e}")
            return []
        

# --------------------
# Async Core Search
# --------------------
async def async_core_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await core_search(query, max_results)
        await log("INFO", "search.py", f"core_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"core_search failed: {e}")
        return []