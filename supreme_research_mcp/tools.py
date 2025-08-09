from web.server import mcp
from akinus_utils.logger import local as log
from supreme_research_mcp.search import run_deep_search
from supreme_research_mcp.record_research import write_data
from akinus_utils.transform.academic import references as refs

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
        deep_search_results = await run_deep_search(query)
        # Example: combine all text results from all queries
        all_texts = []
        all_refs = {}

        for result in deep_search_results:
            all_texts.extend(result["text_results"])
            all_refs.update(result["references"])

        # Format references
        formatted_references = []
        for item in all_refs.values():
            ref_data = {
                "author": ", ".join(item.get("authors", [])) if item.get("authors") else "Unknown Author",
                "year": item.get("year", "n.d."),
                "title": item.get("title", "Untitled"),
                "source": item.get("journal", ""),
                "publisher": "",
                "url": item.get("url", ""),
            }
            formatted = await refs.apa(ref_data)
            formatted_references.append(formatted)

        # Write to file
        data = f"{"\n\n".join(all_texts)}" + f"\n\n" + f"{"\n\n".join(formatted_references)}"
        write_data(f"{data}")

        results = {
            "text_results": f"The user wants you to summarize the following text to answer the query:\n" + "\n".join(all_texts),
            "formatted_references": f"Use these formatted references to provide the user the means to do their own research after you have provided your answer.\n" + "\n".join(formatted_references),
        }

        await log("INFO", "tools.py", f"Deep search completed for query: {query}")
        return results

    except Exception as e:
        await log("ERROR", "tools.py", f"Deep search failed for query {query}: {e}")
        print(f"Deep search failed: {e}")
        return []