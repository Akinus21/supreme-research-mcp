from web.server import mcp
from akinus_utils.logger import local as log
from supreme_research_mcp.search import core_search, arxiv_search, brave_search
from supreme_research_mcp.record_research import write_data
from akinus_utils.transform.academic.references import apa as format_references

@mcp.tool()
async def deep_research(query: str, max_results: int = 10) -> list:
    """
    Perform a deep search on the web for the given query.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
    
    Returns:
        list: A list of search results.
    """
    await log("INFO", "tools.py", f"Performing deep search for query: {query} with max results: {max_results}")
    
    try:
        # Simulate a deep search operation
        
        
        # Here you would implement the actual search logic
        # Call each search
        core_results = core_search(query, max_results)
        arxiv_results = arxiv_search(query, max_results)
        brave_results = brave_search(query, max_results)

        # Add source info
        for r in core_results:
            r["source"] = "core"
        for r in arxiv_results:
            r["source"] = "arxiv"
        for r in brave_results:
            r["source"] = "brave"

        # Combine all results
        combined = core_results + arxiv_results + brave_results

        # Create references list
        references = [format_references(item) for item in combined]

        # Prepare output dict
        results = {
            "query": query,
            "results": combined,
            "references": references
        }

        # Write data to file
        write_data(str(results))
        await log("INFO", "tools.py", f"Deep search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "tools.py", f"Deep search failed: {e}")
        return []