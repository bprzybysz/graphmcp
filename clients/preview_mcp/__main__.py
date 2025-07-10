"""
Main entry point for running the Preview MCP Server standalone.

This allows the server to be run via:
    python -m clients.preview_mcp
"""

import asyncio
import logging
import sys
from .server import MCPWorkflowServer
from .client import GraphMCPWorkflowExecutor

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the Preview MCP Server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting Preview MCP Server...")
    
    try:
        # Create workflow executor
        executor = GraphMCPWorkflowExecutor()
        
        # Create and run MCP server
        server = MCPWorkflowServer(executor, log_level="INFO")
        
        logger.info("Preview MCP Server started successfully on stdio")
        await server.run("stdio")
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 