"""
Main entry point for LiquidPlanner MCP Server
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
