"""
Client Helper Functions for Database Decommissioning.

This module contains MCP client helper functions extracted from repository_processors.py
to maintain the 500-line limit per module.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

# Import MCP clients
from clients import GitHubMCPClient, SlackMCPClient, RepomixMCPClient

# Import new structured logging
from graphmcp.logging import get_logger
from graphmcp.logging.config import LoggingConfig


async def initialize_github_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize GitHub MCP client with proper error handling.
    
    Args:
        context: WorkflowContext for data sharing
        logger: Structured logger instance
        
    Returns:
        GitHubMCPClient instance or None if initialization fails
    """
    try:
        logger.log_info("Initializing GitHub MCP client...")
        github_client = GitHubMCPClient()
        
        # Test connection
        connection_test = await github_client.test_connection()
        if connection_test:
            logger.log_info("GitHub client initialized successfully")
            return github_client
        else:
            logger.log_error("GitHub client connection test failed")
            return None
            
    except Exception as e:
        logger.log_error("Failed to initialize GitHub client", e)
        return None


async def initialize_slack_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize Slack MCP client with proper error handling.
    
    Args:
        context: WorkflowContext for data sharing
        logger: Structured logger instance
        
    Returns:
        SlackMCPClient instance or None if initialization fails
    """
    try:
        logger.log_info("Initializing Slack MCP client...")
        slack_client = SlackMCPClient()
        
        # Test connection
        connection_test = await slack_client.test_connection()
        if connection_test:
            logger.log_info("Slack client initialized successfully")
            return slack_client
        else:
            logger.log_error("Slack client connection test failed")
            return None
            
    except Exception as e:
        logger.log_error("Failed to initialize Slack client", e)
        return None


async def initialize_repomix_client(context: Any, logger: Any) -> Optional[Any]:
    """
    Initialize Repomix MCP client with proper error handling.
    
    Args:
        context: WorkflowContext for data sharing
        logger: Structured logger instance
        
    Returns:
        RepomixMCPClient instance or None if initialization fails
    """
    try:
        logger.log_info("Initializing Repomix MCP client...")
        repomix_client = RepomixMCPClient()
        
        # Test connection
        connection_test = await repomix_client.test_connection()
        if connection_test:
            logger.log_info("Repomix client initialized successfully")
            return repomix_client
        else:
            logger.log_error("Repomix client connection test failed")
            return None
            
    except Exception as e:
        logger.log_error("Failed to initialize Repomix client", e)
        return None


async def send_slack_notification_with_retry(
    slack_client: Any,
    channel: str,
    message: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
    max_retries: int = 3,
    logger: Optional[Any] = None
) -> bool:
    """
    Send Slack notification with retry logic.
    
    Args:
        slack_client: SlackMCPClient instance
        channel: Slack channel to send message to
        message: Message content
        attachments: Optional message attachments
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    for attempt in range(max_retries):
        try:
            await slack_client.send_message(channel, message, attachments or [])
            if logger:
                logger.log_info(f"Slack notification sent successfully (attempt {attempt + 1})")
            return True
        except Exception as e:
            if logger:
                logger.log_warning(f"Slack notification attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                if logger:
                    logger.log_error(f"Failed to send Slack notification after {max_retries} attempts")
                return False
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return False


async def safe_slack_notification(
    slack_client: Any,
    channel: str,
    message: str,
    logger: Any,
    max_retries: int = 3
) -> bool:
    """
    Safely send Slack notification with comprehensive error handling.
    
    Args:
        slack_client: SlackMCPClient instance
        channel: Slack channel to send message to
        message: Message content
        logger: Logger instance
        max_retries: Maximum number of retry attempts
        
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    if not slack_client:
        logger.log_warning("Slack client not available for notification")
        return False
    
    try:
        return await send_slack_notification_with_retry(
            slack_client, channel, message, max_retries=max_retries, logger=logger
        )
    except Exception as e:
        logger.log_error(f"Critical error in Slack notification: {e}")
        return False


def extract_repo_details(repo_url: str) -> Tuple[str, str]:
    """
    Extract owner and repository name from GitHub URL.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Tuple of (owner, repository_name)
    """
    try:
        # Handle different GitHub URL formats
        if "github.com" in repo_url:
            parts = repo_url.split("/")
            if len(parts) >= 4:
                owner = parts[-2]
                repo_name = parts[-1].replace(".git", "")
                return owner, repo_name
        
        # Default fallback
        return "bprzybys-nc", "postgres-sample-dbs"
        
    except Exception:
        return "bprzybys-nc", "postgres-sample-dbs"
