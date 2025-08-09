import os
from dotenv import load_dotenv
import requests
import arxiv
from datetime import datetime
from bs4 import BeautifulSoup
import time
import asyncio
from akinus_utils.app_details import PROJECT_ROOT
from akinus_utils.logger import local as log

# Load environment variables from .env file in the project root
env_file = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    raise FileNotFoundError(f"Environment file not found: {env_file}")

CORE_API_KEY = os.getenv("CORE_API_KEY")

def core_search(query: str, limit: int = 5):
    if not CORE_API_KEY:
        raise ValueError("CORE_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {CORE_API_KEY}"
    }

    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": query,
        "page": 1,
        "pageSize": limit,
        "metadata": "true"
    }

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("results", []):
        authors = item.get("authors", [])
        author_names = [a.get("name") for a in authors if "name" in a]

        year = None
        if "datePublished" in item:
            year = item["datePublished"].split("-")[0]

        meta = {
            "title": item.get("title"),
            "authors": author_names,
            "year": year,
            "journal": item.get("publicationName"),
            "doi": item.get("doi"),
            "url": item.get("openAccessUrl") or item.get("url") or item.get("fullTextUrl"),
            "abstract": item.get("abstract")
        }
        results.append(meta)

    return results

def arxiv_search(query: str, limit: int = 5):
    """
    Search arXiv API and return a list of metadata dicts suitable for APA references and LLM.
    """
    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.Relevance,
        sort_order=arxiv.SortOrder.Descending
    )

    results = []
    for result in search.results():
        # Extract authors as list of full names
        authors = [author.name for author in result.authors]

        # Extract year from published date
        year = result.published.year if result.published else None

        meta = {
            "title": result.title,
            "authors": authors,
            "year": year,
            "journal": "arXiv preprint",
            "doi": result.doi,
            "url": result.pdf_url,
            "abstract": result.summary
        }
        results.append(meta)

    return results

def brave_search(query: str, limit: int = 5):
    """
    Scrape Brave search results for a query, returning a list of metadata dicts.
    Fields standardized for academic references:
    title, authors, year, journal, doi, url, abstract
    """
    base_url = "https://search.brave.com/search"
    params = {
        "q": query,
        "page": 1,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://yourdomain.com/bot)",
        "Accept-Encoding": "gzip, deflate"
    }

    results = []
    while len(results) < limit:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        items = soup.select("div[data-testid='result']")
        if not items:
            break

        for item in items:
            if len(results) >= limit:
                break

            title_tag = item.select_one("a[data-testid='result-title-a']")
            desc_tag = item.select_one("p[data-testid='result-snippet']")
            url = title_tag['href'] if title_tag else None
            title = title_tag.get_text(strip=True) if title_tag else None
            snippet = desc_tag.get_text(strip=True) if desc_tag else None

            # Brave search results do not provide authors, year, journal, or doi info.
            meta = {
                "title": title,
                "authors": [],            # empty list, unknown authors
                "year": None,             # unknown year
                "journal": None,          # unknown journal/source
                "doi": None,              # unknown DOI
                "url": url,
                "abstract": snippet       # use snippet as abstract substitute
            }
            results.append(meta)

        params["page"] += 1
        time.sleep(1)  # polite delay

    return results

async def async_core_search(query, max_results):
    try:
        results = await asyncio.to_thread(core_search, query, max_results)
        await log("INFO", "search.py", f"core_search completed for query: {query}")
        return results
    except Exception as e:
        # Log error and return empty list or None
        await log("ERROR", "search.py", f"core_search failed: {e}")
        print(f"core_search failed: {e}")
        return []

async def async_arxiv_search(query, max_results):
    try:
        results = await asyncio.to_thread(arxiv_search, query, max_results)
        await log("INFO", "search.py", f"arxiv_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"arxiv_search failed: {e}")
        print(f"arxiv_search failed: {e}")
        return []

async def async_brave_search(query, max_results):
    try:
        results = await asyncio.to_thread(brave_search, query, max_results)
        await log("INFO", "search.py", f"brave_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"brave_search failed: {e}")
        print(f"brave_search failed: {e}")
        return []

async def run_all_searches(query, max_results):
    results = await asyncio.gather(
        async_core_search(query, max_results),
        async_arxiv_search(query, max_results),
        async_brave_search(query, max_results),
        return_exceptions=True  # Ensures all run even if one raises
    )

    # results will be a list in order: [core_results, arxiv_results, brave_results]
    # If any raised exceptions, they appear here — but we returned empty lists on except, so should be fine.

    core_results, arxiv_results, brave_results = results

    return core_results, arxiv_results, brave_results