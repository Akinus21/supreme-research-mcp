from web.server import mcp
from akinus_utils.logger import local as log
from supreme_research_mcp.search import run_all_searches
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
        # Extract all text content (abstracts, snippets, etc.) into one list
        research = await run_all_searches(query, max_results)
        
        if not research:
            await log("WARNING", "tools.py", f"No results found for query: {query}")
            return []
        
        text_results = []
        for source_results in (research[0], research[1], research[2]):
            for item in source_results:
                # abstract or snippet or empty string fallback
                text = item.get("abstract") or item.get("snippet") or ""
                if text:
                    text_results.append(text)

        # Extract reference dicts and format them using your APA function
        formatted_references = []
        for source_results in (research[0], research[1], research[2]):
            for item in source_results:
                # Prepare dict for formatting
                ref_data = {
                    "author": ", ".join(item.get("authors", [])) if item.get("authors") else "Unknown Author",
                    "year": item.get("year", "n.d."),
                    "title": item.get("title", "Untitled"),
                    "source": item.get("journal", ""),
                    "publisher": "",   # Not provided by your search results, so empty
                    "url": item.get("url", "")
                }
                # Format reference string
                formatted = format_references(ref_data)
                formatted_references.append(formatted)

        # Write data to file
        write_data("\n\n".join(text_results))  # abstracts and snippets
        write_data("\n\n".join(formatted_references))  # formatted APA refs
        results = {
            "text_results": text_results,
            "formatted_references": formatted_references
        }
        await log("INFO", "tools.py", f"Deep search completed for query: {query}")
        return results
    except Exception as e:
        await log("ERROR", "tools.py", f"Deep search failed: {e}")
        return []