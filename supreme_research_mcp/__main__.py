import sys
import asyncio
from utils import update
from utils.web.server.mcp import mcp
import supreme_research_mcp.tools as tools

async def run_query(query: str):
    print(f"Running deep search for query: {query}\n")
    results = await tools.deep_research(query)
    # Just print the results nicely (or customize)
    import json
    print(json.dumps(results, indent=2))

def main():
    # Run update first (blocking here)
    asyncio.run(update.perform_update())

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        asyncio.run(run_query(query))
        sys.exit(0)

    print("Starting MCP server...")
    mcp.run()
