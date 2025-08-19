from __future__ import annotations
import asyncio
from typing import Dict, Any, List
from akinus.web.scrape.fetch import fetch_url

# --- imports for search runners ---
from akinus.web.search.brave import async_brave_search
from akinus.web.search.duckduckgo import async_duckduckgo_search
from akinus.web.search.openalex import async_openalex_search
from akinus.web.search.arxiv import async_arxiv_search
from akinus.web.search.core import async_core_search
from akinus.web.search.crossref import async_crossref_search

from akinus.utils.logger import log
from supreme_research_mcp.searches.utils import expand_query_ollama
from supreme_research_mcp.searches.utils import refine_results
from supreme_research_mcp.searches.utils import print_results
from akinus.web.server.mcp import mcp
from supreme_research_mcp.searches.extraction import extract_from_url
from akinus.utils.exceptions import ScrapeError
from supreme_research_mcp.searches.constants import *

@mcp.tool()
async def run_deep_research(query: str, limit: int) -> List[Dict[str, Any]]:
    limit = int(limit)
    # Step 1: Expand query
    expanded_queries = await expand_query_ollama(query)
    expanded_queries = expanded_queries[:2]
    expanded_queries.append(query)
    await log("INFO", "run_deep_research", f"Expanded queries: {expanded_queries}")

    all_results: List[Dict[str, Any]] = []

    # Step 2: Concurrency controls
    semaphores = {
        "Brave": asyncio.Semaphore(MAX_CONCURRENT_BRAVE),
        "DuckDuckGo": asyncio.Semaphore(MAX_CONCURRENT_DDG),
        "OpenAlex": asyncio.Semaphore(MAX_CONCURRENT_OPENALEX),
        "arXiv": asyncio.Semaphore(MAX_CONCURRENT_ARXIV),
        "Core": asyncio.Semaphore(MAX_CONCURRENT_CORE),
        "CrossRef": asyncio.Semaphore(MAX_CONCURRENT_CROSSREF),
    }

    async def run_source(source_name: str, func, subquery: str):
        async with semaphores[source_name]:
            attempt = 0
            max_retries = (
                BRAVE_MAX_RETRIES if source_name == "Brave"
                else OPENALEX_MAX_RETRIES if source_name == "OpenAlex"
                else 1
            )
            retry_delay = (
                BRAVE_RETRY_DELAY if source_name == "Brave"
                else OPENALEX_RETRY_DELAY if source_name == "OpenAlex"
                else 0
            )

            while attempt < max_retries:
                try:
                    await log("INFO", "run_deep_research",
                              f"Running {source_name} search for: '{subquery}' attempt {attempt+1}")
                    results = await asyncio.wait_for(func(subquery, limit), timeout=SEARCH_TIMEOUT)
                    if not results:
                        await log("WARNING", "run_deep_research",
                                  f"No results from {source_name} for '{subquery}'")
                        attempt += 1
                        if attempt < max_retries:
                            await asyncio.sleep(retry_delay * attempt)
                            continue
                    for r in results:
                        r["source"] = source_name
                        r["subquery"] = subquery
                    return results
                except asyncio.TimeoutError:
                    await log("WARNING", "run_deep_research",
                              f"{source_name} timed out for '{subquery}'")
                    return []
                except Exception as e:
                    await log("ERROR", "run_deep_research",
                              f"{source_name} failed for '{subquery}' attempt {attempt+1}: {e}")
                    attempt += 1
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * attempt)
                        continue
                    return []

            await log("ERROR", "run_deep_research",
                      f"{source_name} ultimately failed for '{subquery}' after {max_retries} attempts")
            return []

    async def run_sources_for_subquery(subquery: str):
        tasks = [
            run_source("Brave", async_brave_search, subquery),
            run_source("DuckDuckGo", async_duckduckgo_search, subquery),
            run_source("OpenAlex", async_openalex_search, subquery),
            run_source("arXiv", async_arxiv_search, subquery),
            run_source("Core", async_core_search, subquery),
            run_source("CrossRef", async_crossref_search, subquery),
        ]
        return await asyncio.gather(*tasks)

    # Step 3: Run all searches sequentially per subquery
    for subquery in expanded_queries:
        results_nested = await run_sources_for_subquery(subquery)
        for source_results in results_nested:
            all_results.extend(source_results)

    # Step 4: Fetch + extract text concurrently with unified extractor
    async def enrich_with_text(result: Dict[str, Any]) -> Dict[str, Any]:
        url = result.get("url")
        if not url:
            result["text"] = None
            result["chars"] = 0
            return result
        try:
            fetched = await fetch_url(url)
            text = await asyncio.wait_for(extract_from_url(url), timeout=15)
            
            result["text"] = text
            result["chars"] = len(text) if text else 0
        except asyncio.TimeoutError:
            result["text"] = None
            result["chars"] = 0
            result["extraction_error"] = "Timeout after 15 seconds"
        except ScrapeError as e:
            result["text"] = None
            result["chars"] = 0
            result["extraction_error"] = f"ScrapeError: {e}"
        except Exception as e:
            result["text"] = None
            result["chars"] = 0
            result["extraction_error"] = str(e)
        return result

    enriched = await asyncio.gather(*(enrich_with_text(r) for r in all_results))

    # Step 5: Filter low-quality
    filtered_results = [r for r in enriched if r.get("text") and len(r["text"]) > 50]

    # Step 6: Preview
    print_results(filtered_results)

    # Step 7: Refine with embeddings
    refined_results = await refine_results(filtered_results, query, top_k=10, chunk_size=500, overlap=250)

    await log("INFO", "run_deep_research",
              f"Successfully refined top results. Total entries: {len(refined_results)}")
    return refined_results
