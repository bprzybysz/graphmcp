"""
Context7 MCP Client

Specialized client for Context7 documentation MCP server operations.
Implements currently used methods extracted from working db_decommission_workflow.
"""

import logging
from pathlib import Path
from typing import Any

from ..utils import Context7Documentation, ensure_serializable
from .base import BaseMCPClient

logger = logging.getLogger(__name__)


class Context7MCPClient(BaseMCPClient):
    """
    Specialized MCP client for Context7 documentation server operations.
    
    Implements the exact patterns and methods currently used in 
    db_decommission_workflow for maximum compatibility.
    """

    def __init__(self, config_path: str | Path, server_name: str = "ovr_context7"):
        """
        Initialize Context7 MCP client.
        
        Args:
            config_path: Path to MCP configuration file
            server_name: Name of Context7 server in config (default: "ovr_context7")
        """
        super().__init__(config_path, server_name)

    async def get_library_docs(
        self, 
        library_id: str, 
        topic: str | None = None, 
        tokens: int = 10000
    ) -> Context7Documentation:
        """
        Get documentation for a specific library from Context7.
        
        Args:
            library_id: Context7-compatible library ID (e.g., "/mongodb/docs")
            topic: Optional topic to focus documentation on
            tokens: Maximum tokens of documentation to retrieve
            
        Returns:
            Context7Documentation object with extracted content
        """
        params = {
            "context7CompatibleLibraryID": library_id,
            "tokens": tokens
        }
        
        if topic:
            params["topic"] = topic

        try:
            logger.debug(f"Calling get-library-docs for library_id: {library_id}, topic: {topic}")
            raw_result = await self.call_tool_with_retry("get-library-docs", params)

            # Extract content exactly as in DirectMCPClient.call_context7_tools()
            extracted_content = []
            content_summary = "No documentation found"
            
            if raw_result and hasattr(raw_result, 'content') and isinstance(raw_result.content, list):
                for item in raw_result.content:
                    if hasattr(item, 'text') and isinstance(item.text, str):
                        extracted_content.append(item.text)

                if extracted_content:
                    combined_content = "\n\n----------------------------------------\n\n".join(extracted_content)
                    content_summary = f"Retrieved {len(extracted_content)} documentation sections"
                    logger.info(f"Successfully extracted detailed Context7 documentation for {library_id}")
                else:
                    logger.warning(f"get-library-docs returned empty content for {library_id}")
                    content_summary = f"No detailed documentation found for {library_id} on topic {topic or 'general'}"
            else:
                logger.warning(f"get-library-docs returned unexpected format for {library_id}: {raw_result}")
                content_summary = f"No detailed documentation found for {library_id} on topic {topic or 'general'}"

            # Create result object
            result = Context7Documentation(
                library_id=library_id,
                topic=topic or "general",
                content_sections=extracted_content,
                summary=content_summary
            )

            # Ensure result is serializable
            ensure_serializable(result)
            return result

        except Exception as e:
            logger.error(f"Failed to get library docs for {library_id}: {e}")
            
            # Return error result
            error_result = Context7Documentation(
                library_id=library_id,
                topic=topic or "general",
                content_sections=[],
                summary=f"Error retrieving documentation: {e}"
            )
            ensure_serializable(error_result)
            return error_result

    async def search_documentation(
        self,
        search_query: str,
        library_id: str | None = None,
        topic: str | None = None,
        max_retries: int = 3
    ) -> str:
        """
        Search documentation using Context7 with exact DirectMCPClient patterns.
        
        Args:
            search_query: Search query for documentation
            library_id: Optional specific library to search
            topic: Optional topic to focus on
            max_retries: Maximum retry attempts
            
        Returns:
            Documentation search results as string
        """
        try:
            results = []

            # If library_id is provided, get specific documentation
            if library_id:
                docs = await self.get_library_docs(library_id, topic)
                
                if docs.content_sections:
                    combined_content = "\n\n----------------------------------------\n\n".join(docs.content_sections)
                    results.append(combined_content)
                else:
                    results.append(docs.summary)

            if results:
                final_result = "\n\n".join(results)
                ensure_serializable(final_result)
                logger.info(f"Successfully executed Context7 documentation search")
                return final_result
            else:
                fallback_result = f"Documentation search completed for '{search_query}' - tools executed but no detailed results available"
                ensure_serializable(fallback_result)
                return fallback_result

        except Exception as e:
            logger.error(f"Context7 documentation search failed: {e}")
            raise RuntimeError(f"Context7 search execution failed: {e}")

    async def resolve_library_id(self, library_name: str) -> str | None:
        """
        Resolve a library name to a Context7-compatible library ID.
        
        This is a placeholder for future implementation of the resolve-library-id tool.
        Currently returns None since this tool isn't used in the current workflow.
        
        Args:
            library_name: Name of the library to resolve
            
        Returns:
            Context7-compatible library ID or None if not found
        """
        logger.warning(f"resolve_library_id not implemented yet for library: {library_name}")
        return None

    # Legacy compatibility method - maintains exact interface
    async def call_context7_tools(
        self,
        search_query: str,
        library_id: str | None = None,
        topic: str | None = None,
        max_retries: int = 3
    ) -> str:
        """
        Legacy compatibility method that maintains exact DirectMCPClient interface.
        
        This method exists for backward compatibility with existing code
        that expects the original call_context7_tools() interface.
        
        Args:
            search_query: Search query for documentation
            library_id: Optional Context7-compatible library ID
            topic: Optional topic to focus on
            max_retries: Maximum retry attempts
            
        Returns:
            Documentation results as string (exact format as DirectMCPClient)
        """
        try:
            return await self.search_documentation(search_query, library_id, topic, max_retries)
        except Exception as e:
            logger.error(f"Legacy Context7 tools call failed: {e}")
            raise RuntimeError(f"Context7 tools execution failed: {e}")

    async def get_available_libraries(self) -> list[str]:
        """
        Get list of available libraries (placeholder for future implementation).
        
        This would use a list-libraries tool if available in the future.
        Currently returns empty list since this isn't used in current workflow.
        
        Returns:
            List of available library IDs
        """
        logger.warning("get_available_libraries not implemented yet")
        return [] 