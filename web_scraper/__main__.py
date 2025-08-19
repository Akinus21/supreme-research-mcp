# main.py
import sys
import asyncio
from akinus.web.server.mcp import *

# Import tools so they get registered via decorators
import web_scraper.tools.deep_research as mcp_tools

def main():

    tools = discover_mcp_tools(mcp_tools)

    print(tools)

    # If no CLI args, run MCP server
    if len(sys.argv) == 1:
        mcp.run()
    else:
        parser = build_cli_parser(tools)
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            sys.exit(1)

        # Run the selected tool asynchronously
        asyncio.run(run_cli_tool(tools[args.command], args))

if __name__ == "__main__":
    main()
