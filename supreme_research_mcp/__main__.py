import asyncio
from akinus_utils import update
from web.server import mcp
import supreme_research_mcp.tools as tools

def main():
    # Run update check at start (non-blocking if you want, or blocking)
    asyncio.run(update.perform_update())

    # Your existing CLI logic
    print("Hello from my_project CLI!")

    mcp.run()  # Start the MCP server
