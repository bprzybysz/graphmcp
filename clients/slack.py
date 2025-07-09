"""
Slack MCP Client

Specialized client for Slack MCP server operations.
Enables AI assistants to interact with Slack workspaces through
the Slack MCP server implementation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils import ensure_serializable
from .base import BaseMCPClient, MCPToolError

logger = logging.getLogger(__name__)

class SlackMCPClient(BaseMCPClient):
    """
    Specialized MCP client for Slack server operations.
    
    Provides tools for posting messages, managing channels,
    reactions, and other Slack workspace interactions.
    """
    SERVER_NAME = "slack"
    
    def __init__(self, config_path: str | Path):
        """
        Initialize Slack MCP client.
        
        Args:
            config_path: Path to MCP configuration file
        """
        super().__init__(config_path)

    async def list_available_tools(self) -> List[str]:
        """List available Slack MCP tools."""
        try:
            result = await self._send_mcp_request("tools/list", {})
            return [tool.get("name") for tool in result.get("tools", [])]
        except Exception as e:
            logger.warning(f"Failed to list Slack tools: {e}")
            return [
                "post_message",
                "list_channels", 
                "add_reaction",
                "get_channel_history",
                "list_users",
                "create_channel",
                "invite_user_to_channel"
            ]

    async def post_message(self, channel_id: str, text: str, 
                          thread_ts: Optional[str] = None,
                          blocks: Optional[List[Dict]] = None,
                          attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Post a message to a Slack channel.
        
        Args:
            channel_id: Slack channel ID (e.g., "C01234567") or channel name
            text: Message text to post
            thread_ts: Optional thread timestamp for threaded replies
            blocks: Optional blocks for rich message formatting
            attachments: Optional message attachments (legacy)
            
        Returns:
            Message posting result with metadata
        """
        params = {
            "channel": channel_id,
            "text": text
        }
        
        if thread_ts:
            params["thread_ts"] = thread_ts
        if blocks:
            params["blocks"] = blocks
        if attachments:
            params["attachments"] = attachments
            
        try:
            result = await self.call_tool_with_retry("post_message", params)
            
            message_result = {
                "success": result.get("ok", False),
                "channel": channel_id,
                "ts": result.get("ts"),
                "message": {
                    "text": text,
                    "ts": result.get("ts"),
                    "user": result.get("message", {}).get("user"),
                    "bot_id": result.get("message", {}).get("bot_id")
                }
            }
            
            if thread_ts:
                message_result["thread_ts"] = thread_ts
            
            ensure_serializable(message_result)
            
            if message_result["success"]:
                logger.info(f"Posted message to channel {channel_id}")
            else:
                logger.warning(f"Failed to post message: {result.get('error', 'Unknown error')}")
                message_result["error"] = result.get("error", "Unknown error")
            
            return message_result
            
        except Exception as e:
            logger.error(f"Failed to post message to {channel_id}: {e}")
            return {
                "success": False, 
                "channel": channel_id, 
                "error": str(e)
            }

    async def list_channels(self, types: str = "public_channel,private_channel",
                           exclude_archived: bool = True,
                           limit: int = 1000) -> List[Dict[str, Any]]:
        """
        List available Slack channels.
        
        Args:
            types: Comma-separated list of channel types to include
            exclude_archived: Whether to exclude archived channels
            limit: Maximum number of channels to return
            
        Returns:
            List of channel information dictionaries
        """
        params = {
            "types": types,
            "exclude_archived": exclude_archived,
            "limit": limit
        }
        
        try:
            result = await self.call_tool_with_retry("list_channels", params)
            
            if result.get("ok"):
                channels = []
                for channel in result.get("channels", []):
                    channel_info = {
                        "id": channel.get("id"),
                        "name": channel.get("name"),
                        "is_channel": channel.get("is_channel", False),
                        "is_group": channel.get("is_group", False), 
                        "is_im": channel.get("is_im", False),
                        "is_private": channel.get("is_private", False),
                        "is_archived": channel.get("is_archived", False),
                        "is_general": channel.get("is_general", False),
                        "num_members": channel.get("num_members", 0),
                        "topic": channel.get("topic", {}).get("value", ""),
                        "purpose": channel.get("purpose", {}).get("value", ""),
                        "created": channel.get("created")
                    }
                    channels.append(channel_info)
                
                ensure_serializable(channels)
                logger.debug(f"Retrieved {len(channels)} channels")
                return channels
            else:
                logger.warning(f"Failed to list channels: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            return []

    async def add_reaction(self, channel: str, timestamp: str, name: str) -> Dict[str, Any]:
        """
        Add an emoji reaction to a message.
        
        Args:
            channel: Slack channel ID or name
            timestamp: Message timestamp
            name: Emoji name (without colons, e.g., "thumbsup")
            
        Returns:
            Reaction addition result
        """
        params = {
            "channel": channel,
            "timestamp": timestamp,
            "name": name
        }
        
        try:
            result = await self.call_tool_with_retry("add_reaction", params)
            
            reaction_result = {
                "success": result.get("ok", False),
                "channel": channel,
                "timestamp": timestamp,
                "reaction": name
            }
            
            if not reaction_result["success"]:
                reaction_result["error"] = result.get("error", "Unknown error")
                logger.warning(f"Failed to add reaction {name}: {reaction_result['error']}")
            else:
                logger.debug(f"Added reaction {name} to message in {channel}")
            
            ensure_serializable(reaction_result)
            return reaction_result
            
        except Exception as e:
            logger.error(f"Failed to add reaction {name}: {e}")
            return {
                "success": False,
                "channel": channel,
                "timestamp": timestamp,
                "reaction": name,
                "error": str(e)
            }

    async def get_channel_history(self, channel: str, limit: int = 100,
                                 latest: Optional[str] = None,
                                 oldest: Optional[str] = None,
                                 include_all_metadata: bool = False) -> Dict[str, Any]:
        """
        Get recent messages from a channel.
        
        Args:
            channel: Slack channel ID or name
            limit: Maximum number of messages to retrieve (max 1000)
            latest: End of time range of messages to include
            oldest: Start of time range of messages to include
            include_all_metadata: Whether to include all message metadata
            
        Returns:
            Channel history with messages and metadata
        """
        params = {
            "channel": channel,
            "limit": min(limit, 1000),
            "include_all_metadata": include_all_metadata
        }
        
        if latest:
            params["latest"] = latest
        if oldest:
            params["oldest"] = oldest
        
        try:
            result = await self.call_tool_with_retry("get_channel_history", params)
            
            if result.get("ok"):
                messages = []
                for msg in result.get("messages", []):
                    message_info = {
                        "type": msg.get("type", "message"),
                        "user": msg.get("user"),
                        "text": msg.get("text", ""),
                        "ts": msg.get("ts"),
                        "thread_ts": msg.get("thread_ts"),
                        "reply_count": msg.get("reply_count", 0),
                        "replies": msg.get("replies", []),
                        "bot_id": msg.get("bot_id"),
                        "username": msg.get("username"),
                        "reactions": msg.get("reactions", [])
                    }
                    
                    # Include additional metadata if requested
                    if include_all_metadata:
                        message_info.update({
                            "edited": msg.get("edited"),
                            "attachments": msg.get("attachments", []),
                            "blocks": msg.get("blocks", []),
                            "files": msg.get("files", [])
                        })
                    
                    messages.append(message_info)
                
                history_result = {
                    "success": True,
                    "channel": channel,
                    "messages": messages,
                    "has_more": result.get("has_more", False),
                    "pin_count": result.get("pin_count", 0)
                }
                
                ensure_serializable(history_result)
                logger.debug(f"Retrieved {len(messages)} messages from {channel}")
                return history_result
            else:
                error = result.get("error", "Unknown error")
                logger.warning(f"Failed to get channel history: {error}")
                return {
                    "success": False,
                    "channel": channel,
                    "messages": [],
                    "error": error
                }
                
        except Exception as e:
            logger.error(f"Failed to get channel history for {channel}: {e}")
            return {
                "success": False,
                "channel": channel,
                "messages": [],
                "error": str(e)
            }

    async def list_users(self, limit: int = 1000,
                        include_locale: bool = False) -> List[Dict[str, Any]]:
        """
        List users in the Slack workspace.
        
        Args:
            limit: Maximum number of users to return
            include_locale: Whether to include user locale information
            
        Returns:
            List of user information dictionaries
        """
        params = {
            "limit": limit,
            "include_locale": include_locale
        }
        
        try:
            result = await self.call_tool_with_retry("list_users", params)
            
            if result.get("ok"):
                users = []
                for user in result.get("members", []):
                    user_info = {
                        "id": user.get("id"),
                        "name": user.get("name"),
                        "real_name": user.get("real_name"),
                        "display_name": user.get("profile", {}).get("display_name", ""),
                        "email": user.get("profile", {}).get("email"),
                        "is_bot": user.get("is_bot", False),
                        "is_admin": user.get("is_admin", False),
                        "is_owner": user.get("is_owner", False),
                        "is_restricted": user.get("is_restricted", False),
                        "is_ultra_restricted": user.get("is_ultra_restricted", False),
                        "deleted": user.get("deleted", False),
                        "tz": user.get("tz"),
                        "tz_label": user.get("tz_label")
                    }
                    
                    if include_locale:
                        user_info["locale"] = user.get("locale")
                    
                    users.append(user_info)
                
                ensure_serializable(users)
                logger.debug(f"Retrieved {len(users)} users")
                return users
            else:
                logger.warning(f"Failed to list users: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            return []

    async def create_channel(self, name: str, is_private: bool = False) -> Dict[str, Any]:
        """
        Create a new Slack channel.
        
        Args:
            name: Channel name (must be lowercase, no spaces)
            is_private: Whether to create a private channel
            
        Returns:
            Channel creation result
        """
        params = {
            "name": name,
            "is_private": is_private
        }
        
        try:
            result = await self.call_tool_with_retry("create_channel", params)
            
            create_result = {
                "success": result.get("ok", False),
                "channel": result.get("channel", {}),
                "name": name,
                "is_private": is_private
            }
            
            if not create_result["success"]:
                create_result["error"] = result.get("error", "Unknown error")
                logger.warning(f"Failed to create channel {name}: {create_result['error']}")
            else:
                logger.info(f"Created channel: {name}")
            
            ensure_serializable(create_result)
            return create_result
            
        except Exception as e:
            logger.error(f"Failed to create channel {name}: {e}")
            return {
                "success": False,
                "name": name,
                "error": str(e)
            }

    async def invite_user_to_channel(self, channel: str, user: str) -> Dict[str, Any]:
        """
        Invite a user to a channel.
        
        Args:
            channel: Channel ID or name
            user: User ID to invite
            
        Returns:
            Invitation result
        """
        params = {
            "channel": channel,
            "user": user
        }
        
        try:
            result = await self.call_tool_with_retry("invite_user_to_channel", params)
            
            invite_result = {
                "success": result.get("ok", False),
                "channel": channel,
                "user": user
            }
            
            if not invite_result["success"]:
                invite_result["error"] = result.get("error", "Unknown error")
                logger.warning(f"Failed to invite user {user} to {channel}: {invite_result['error']}")
            else:
                logger.info(f"Invited user {user} to channel {channel}")
            
            ensure_serializable(invite_result)
            return invite_result
            
        except Exception as e:
            logger.error(f"Failed to invite user {user} to channel {channel}: {e}")
            return {
                "success": False,
                "channel": channel,
                "user": user,
                "error": str(e)
            } 