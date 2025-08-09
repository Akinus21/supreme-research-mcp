import os
from dotenv import load_dotenv
import requests
import arxiv
from datetime import datetime
from bs4 import BeautifulSoup
import time

# Load environment variables from .env file in the project root
load_dotenv()

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
    """
    base_url = "https://search.brave.com/search"
    params = {
        "q": query,
        "page": 1,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://yourdomain.com/bot)"
    }

    results = []
    while len(results) < limit:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Find result containers
        items = soup.select("div[data-testid='result']")

        if not items:
            # No results found or page structure changed
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
                "url": url,
                "snippet": snippet
            })

        # Go to next page if needed
        params["page"] += 1
        time.sleep(1)  # polite delay

    return results