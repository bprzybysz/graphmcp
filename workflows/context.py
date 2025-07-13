"""
WorkflowContext for GraphMCP workflows.

This module provides the WorkflowContext dataclass for sharing data between
workflow steps following GraphMCP serialization patterns.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from utils import ensure_serializable


@dataclass
class WorkflowContext:
    """
    Shared data context for workflow steps.
    
    Provides safe serialization and data sharing between workflow steps
    following GraphMCP patterns for state management.
    
    Args:
        data: Dictionary of step data, automatically serialized for safety
        metadata: Workflow metadata (timestamps, execution info, etc.)
        created_at: Timestamp when context was created
        last_updated: Timestamp when context was last modified
    """
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[float] = None
    last_updated: Optional[float] = None

    def __post_init__(self):
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = time.time()
        if self.last_updated is None:
            self.last_updated = self.created_at

    def set(self, key: str, value: Any) -> None:
        """
        Set context data with serialization safety.
        
        Args:
            key: Data key
            value: Data value (will be made serializable)
        """
        self.data[key] = ensure_serializable(value)
        self.last_updated = time.time()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get context data.
        
        Args:
            key: Data key
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if context has a key.
        
        Args:
            key: Data key to check
            
        Returns:
            True if key exists
        """
        return key in self.data

    def remove(self, key: str) -> Any:
        """
        Remove and return data for a key.
        
        Args:
            key: Data key to remove
            
        Returns:
            Removed value or None if key not found
        """
        value = self.data.pop(key, None)
        if value is not None:
            self.last_updated = time.time()
        return value

    def update_metadata(self, **kwargs) -> None:
        """
        Update metadata with new values.
        
        Args:
            **kwargs: Metadata key-value pairs
        """
        self.metadata.update(kwargs)
        self.last_updated = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format for serialization.
        
        Returns:
            Dictionary representation with serialization safety
        """
        return {
            "data": ensure_serializable(self.data),
            "metadata": ensure_serializable(self.metadata),
            "created_at": self.created_at,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowContext':
        """
        Create WorkflowContext from dictionary.
        
        Args:
            data: Dictionary with context data
            
        Returns:
            WorkflowContext instance
        """
        return cls(
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at"),
            last_updated=data.get("last_updated"),
        )

    def __getstate__(self):
        """Custom pickling to ensure serialization safety."""
        state = self.__dict__.copy()
        # Ensure all data is serializable
        state['data'] = ensure_serializable(state['data'])
        state['metadata'] = ensure_serializable(state['metadata'])
        return state

    def __setstate__(self, state):
        """Custom unpickling to restore state."""
        self.__dict__.update(state)