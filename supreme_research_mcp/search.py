
import asyncio
from utils.app_details import PROJECT_ROOT
from utils.logger import local as log
from supreme_research_mcp.ollama import generate_search_queries
import json
import re
from utils.web.search.crossref import async_crossref_search
from utils.web.search.open_alex import async_openalex_search
from utils.web.search.brave import async_brave_search
from utils.web.search.core import async_core_search
from utils.web.search.arxiv import async_arxiv_search
from utils.ai.ollama import ollama_query

# --------------------
# helpers
# --------------------
def sanitize_query(query: str) -> str:
    query = re.sub(r"[`\"'\n\r]", " ", query)
    query = re.sub(r"\s+", " ", query).strip()
    return query

async def generate_search_queries(original_query: str) -> list[str]:
    prompt = f"""
Given the user query below, generate exactly 3 distinct, concise, and focused search queries that capture the intent and keywords needed to find relevant scholarly or trusted sources.  
Return only the queries as a JSON list of strings.

User query:
\"\"\"{original_query}\"\"\"

Search queries:"""

    response_text = await ollama_query(prompt)  # Your function that calls ollama CLI
    
    # Strip markdown backticks (``` or ```json)
    cleaned_response = re.sub(r"^```(?:json)?\n?|```$", "", response_text.strip(), flags=re.MULTILINE)

    try:
        queries = json.loads(cleaned_response)
        if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
            raise ValueError("Parsed JSON is not a list of strings")
        return queries
    except Exception:
        await log("ERROR", "ollama.py", f"Failed to parse Ollama response: {response_text}")
        # fallback: try to parse lines starting with '- ' or just split lines
        lines = [line.strip("- ").strip() for line in cleaned_response.splitlines() if line.strip()]
        if len(lines) >= 3:
            return lines[:3]
        return [original_query] * 3

# --------------------
# Master search runner
# --------------------
async def run_all_searches(query: str, max_results: int = 5) -> dict:
    """
    Run CrossRef, arXiv, Brave, OpenAlex, and CORE searches concurrently.
    """
    results = await asyncio.gather(
        async_crossref_search(query, max_results),
        async_arxiv_search(query, max_results),
        async_brave_search(query, max_results),
        async_openalex_search(query, max_results),
        async_core_search(query, max_results),
        return_exceptions=True,
    )

    crossref_results = results[0] if not isinstance(results[0], Exception) else []
    arxiv_results = results[1] if not isinstance(results[1], Exception) else []
    brave_results = results[2] if not isinstance(results[2], Exception) else []
    openalex_results = results[3] if not isinstance(results[3], Exception) else []
    core_results = results[4] if not isinstance(results[4], Exception) else []

    text_results = []
    references_dict = {}

    def add_reference(item):
        key = item.get("doi") or f"{item.get('title', '')}_{item.get('year', '')}"
        if key not in references_dict:
            references_dict[key] = item
            abstract = item.get("abstract")
            if abstract:
                text_results.append(abstract)

    for source_results in [crossref_results, arxiv_results, brave_results, openalex_results, core_results]:
        for item in source_results:
            add_reference(item)

    return {
        "crossref": crossref_results,
        "arxiv": arxiv_results,
        "brave": brave_results,
        "openalex": openalex_results,
        "core": core_results,
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
                **result,
            })
        return all_results
    except Exception as e:
        raise RuntimeError(f"run_deep_search failed: {e}")
