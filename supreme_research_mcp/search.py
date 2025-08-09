import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Tuple
import requests
import arxiv
from datetime import datetime
from bs4 import BeautifulSoup
import time
import asyncio
from akinus_utils.app_details import PROJECT_ROOT
from akinus_utils.logger import local as log
from supreme_research_mcp.ollama import generate_search_queries

# Load environment variables from .env file in the project root
env_file = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
else:
    raise FileNotFoundError(f"Environment file not found: {env_file}")

# --------------------
# Semantic Scholar Search (with full abstract fetch)
# --------------------
def semantic_scholar_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Semantic Scholar API for papers, then fetch full abstracts if missing.
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,authors,year,abstract,url,venue,doi"
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", [])

    results = []
    for paper in data:
        authors = [a["name"] for a in paper.get("authors", [])]
        abstract = paper.get("abstract")

        # If no abstract, fetch the full record
        if not abstract and paper.get("paperId"):
            try:
                detail_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper['paperId']}"
                detail_params = {"fields": "abstract"}
                detail_r = requests.get(detail_url, params=detail_params, timeout=10)
                detail_r.raise_for_status()
                abstract = detail_r.json().get("abstract")
            except Exception:
                abstract = None

        results.append({
            "title": paper.get("title"),
            "authors": authors,
            "year": paper.get("year"),
            "journal": paper.get("venue"),
            "doi": paper.get("doi"),
            "url": paper.get("url"),
            "abstract": abstract,
        })
    return results


# --------------------
# CrossRef Search (with abstract parsing)
# --------------------
def crossref_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search CrossRef API for papers and parse abstracts when available.
    """
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": limit}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    items = r.json().get("message", {}).get("items", [])

    results = []
    for item in items:
        authors = []
        for a in item.get("author", []):
            name_parts = [a.get("given", ""), a.get("family", "")]
            authors.append(" ".join([p for p in name_parts if p]))

        year = None
        if "published-print" in item:
            year = item["published-print"]["date-parts"][0][0]
        elif "published-online" in item:
            year = item["published-online"]["date-parts"][0][0]

        # Parse abstract if available
        abstract_raw = item.get("abstract")
        abstract = None
        if abstract_raw:
            try:
                soup = BeautifulSoup(abstract_raw, "html.parser")
                abstract = soup.get_text(" ", strip=True)
            except Exception:
                abstract = abstract_raw  # fallback

        results.append({
            "title": item.get("title", [None])[0],
            "authors": authors,
            "year": year,
            "journal": item.get("container-title", [None])[0],
            "doi": item.get("DOI"),
            "url": item.get("URL"),
            "abstract": abstract,
        })
    return results

# --------------------
# arXiv Search
# --------------------
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
        authors = [author.name for author in result.authors]
        year = result.published.year if result.published else None
        results.append({
            "title": result.title,
            "authors": authors,
            "year": year,
            "journal": "arXiv preprint",
            "doi": result.doi,
            "url": result.pdf_url,
            "abstract": result.summary
        })
    return results

# --------------------
# Brave Search
# --------------------
def brave_search(query: str, limit: int = 5):
    """
    Scrape Brave search results for a query, returning a list of metadata dicts.
    """
    base_url = "https://search.brave.com/search"
    params = {"q": query, "page": 1}
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
            results.append({
                "title": title,
                "authors": [],
                "year": None,
                "journal": None,
                "doi": None,
                "url": url,
                "abstract": snippet
            })
        params["page"] += 1
        time.sleep(1)  # polite delay
    return results

# --------------------
# Async wrappers
# --------------------
async def async_semantic_scholar_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await asyncio.to_thread(semantic_scholar_search, query, max_results)
        await log("INFO", "search.py", f"semantic_scholar_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"semantic_scholar_search failed: {e}")
        print(f"semantic_scholar_search failed: {e}")
        raise

async def async_crossref_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await asyncio.to_thread(crossref_search, query, max_results)
        await log("INFO", "search.py", f"crossref_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"crossref_search failed: {e}")
        print(f"crossref_search failed: {e}")
        raise

async def async_arxiv_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await asyncio.to_thread(arxiv_search, query, max_results)
        await log("INFO", "search.py", f"arxiv_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"arxiv_search failed: {e}")
        print(f"arxiv_search failed: {e}")
        raise

async def async_brave_search(query: str, max_results: int) -> List[Dict[str, Any]]:
    try:
        results = await asyncio.to_thread(brave_search, query, max_results)
        await log("INFO", "search.py", f"brave_search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "search.py", f"brave_search failed: {e}")
        print(f"brave_search failed: {e}")
        raise

# --------------------
# Master search runner with extraction of text_results and references_dict
# --------------------
async def run_all_searches(
    query: str, max_results: int = 5
) -> dict:
    """
    Run Semantic Scholar, CrossRef, arXiv, and Brave searches concurrently.
    Return a dict with:
      - 'text_results': list of abstracts/snippets
      - 'references': dict of metadata keyed by DOI or title+year
    """
    results = await asyncio.gather(
        async_semantic_scholar_search(query, max_results),
        async_crossref_search(query, max_results),
        async_arxiv_search(query, max_results),
        async_brave_search(query, max_results),
        return_exceptions=True,
    )

    semantic_results, crossref_results, arxiv_results, brave_results = results

    text_results = []
    references_dict = {}

    def add_reference(item):
        key = item.get("doi") or f"{item.get('title', '')}_{item.get('year', '')}"
        if key not in references_dict:
            references_dict[key] = item
            abstract = item.get("abstract")
            if abstract:
                text_results.append(abstract)

    for source_results in [semantic_results, crossref_results, arxiv_results, brave_results]:
        if isinstance(source_results, Exception):
            continue
        for item in source_results:
            add_reference(item)

    return {
        "semantic": semantic_results,
        "crossref": crossref_results,
        "arxiv": arxiv_results,
        "brave": brave_results,
        "text_results": text_results,
        "references": references_dict,
    }

async def run_deep_search(original_query: str, max_results_per_query: int = 20):
    queries = await generate_search_queries(original_query)
    all_results = []
    try:
        for q in queries:
            result = await run_all_searches(q, max_results_per_query)
            all_results.append({
                "query": q,
                **result,  # unpack keys like 'semantic', 'crossref', 'text_results', etc.
            })
        return all_results
    except Exception as e:
        raise RuntimeError(f"run_deep_search failed: {e}")
