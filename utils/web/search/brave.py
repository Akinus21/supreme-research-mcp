from utils.logger import local as log
import asyncio
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import time

# --------------------
# Brave Search
# --------------------
def brave_search(query: str, limit: int = 5, max_retries: int = 5, backoff_factor: float = 1.0) -> List[Dict[str, Any]]:
    base_url = "https://search.brave.com/search"
    params = {"q": query, "page": 1}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://yourdomain.com/bot)",
        "Accept-Encoding": "gzip, deflate"
    }

    results = []
    while len(results) < limit:
        attempt = 0
        while attempt <= max_retries:
            try:
                response = requests.get(base_url, params=params, headers=headers)
                if response.status_code == 429:
                    # Too Many Requests - retry after backoff
                    wait_time = backoff_factor * (2 ** attempt)
                    attempt += 1
                    time.sleep(wait_time)
                    continue
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                items = soup.select("div[data-testid='result']")
                if not items:
                    # No results found - break out of the retry loop & pagination
                    return results

                for item in items:
                    if len(results) >= limit:
                        break
                    title_tag = item.select_one("a[data-testid='result-title-a']")
                    desc_tag = item.select_one("p[data-testid='result-snippet']")
                    url = title_tag['href'] if title_tag else None
                    title = title_tag.get_text(strip=True) if title_tag else None
                    snippet = desc_tag.get_text(strip=True) if desc_tag else None
                    results.append({
                        "title": title,
                        "authors": [],
                        "year": None,
                        "journal": None,
                        "doi": None,
                        "url": url,
                        "abstract": snippet
                    })

                # Success, break retry loop to go to next page
                break

            except requests.RequestException as e:
                # For network-related errors or others, retry with backoff
                attempt += 1
                if attempt > max_retries:
                    raise  # Raise if max retries exceeded
                wait_time = backoff_factor * (2 ** (attempt - 1))
                time.sleep(wait_time)

        params["page"] += 1

    return results

# --------------------
# Async Brave Search
# --------------------
async def async_brave_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await asyncio.to_thread(brave_search, query, max_results)
        await log("INFO", "search.py", f"brave_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"brave_search failed: {e}")
        return []