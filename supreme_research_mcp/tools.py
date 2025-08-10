from utils.web.server import mcp
from utils.logger import local as log
from supreme_research_mcp.search import run_deep_search
from utils.transform.academic import references as refs
from utils.app_details import PROJECT_ROOT

@mcp.tool()
async def deep_research(query: str, max_results: int = 10) -> dict:
    """
    Perform a deep search on the web for the given query.
    
    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to return.
    
    Returns:
        dict: Contains concatenated text results and formatted references.
    """
    await log("INFO", "tools.py", f"Performing deep search for query: {query} with max results: {max_results}")

    try:
        deep_search_results = await run_deep_search(query)

        all_texts = []
        all_refs = {}

        # Normalize search results
        for result in deep_search_results:
            raw_texts = result.get("text_results", [])
            if raw_texts:
                normalized_texts = []
                for item in raw_texts:
                    if isinstance(item, dict):
                        title = item.get("title", "").strip()
                        snippet = item.get("snippet", "").strip()
                        url = item.get("url", "").strip()
                        combined = " - ".join(filter(None, [title, snippet]))
                        if url:
                            combined += f" ({url})"
                        if combined:
                            normalized_texts.append(combined)
                    else:
                        normalized_texts.append(str(item).strip())
                all_texts.extend(t for t in normalized_texts if t)

            # Merge references
            refs_dict = result.get("references", {})
            if isinstance(refs_dict, dict):
                all_refs.update(refs_dict)

        # Format references safely
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
            try:
                formatted = await refs.apa(ref_data)
                formatted_references.append(formatted)
            except Exception as e:
                await log("ERROR", "tools.py", f"Reference formatting failed: {e}")

        # Prepare output
        all_text_str = "\n\n".join(all_texts)
        all_refs_str = "\n\n".join(formatted_references)

        # Write to file for record-keeping
        data_to_write = f"{all_text_str}\n\n{all_refs_str}"
        write_data(data_to_write)

        results = {
            "text_results": (
                "The user wants you to summarize the following text to answer the query:\n" +
                all_text_str
            ),
            "formatted_references": (
                "Use these formatted references to provide the user the means to do their own research "
                "after you have provided your answer.\n" +
                all_refs_str
            ),
        }

        await log("INFO", "tools.py", f"Deep search completed for query: {query}")
        return results

    except Exception as e:
        await log("ERROR", "tools.py", f"Deep search failed for query {query}: {e}")
        print(f"Deep search failed: {e}")
        return {}

def write_data(data):
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_FILE = DATA_DIR / "data.txt"

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w') as file:
        file.write(data)