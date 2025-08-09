import asyncio
from supreme_research_mcp.utils import update

def main():
    # Run update check at start (non-blocking if you want, or blocking)
    asyncio.run(update.perform_update())

    # Your existing CLI logic
    print("Hello from my_project CLI!")
