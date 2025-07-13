"""
Unit tests for WorkflowContext.

Tests the WorkflowContext dataclass serialization, data management,
and integration with the GraphMCP framework.
"""

import pytest
import time
from typing import Dict, Any

from workflows.context import WorkflowContext


class TestWorkflowContext:
    """Test suite for WorkflowContext functionality."""
    
    def test_context_initialization(self):
        """Test WorkflowContext initializes correctly."""
        ctx = WorkflowContext()
        
        assert isinstance(ctx.data, dict)
        assert isinstance(ctx.metadata, dict)
        assert ctx.created_at is not None
        assert ctx.last_updated is not None
        assert ctx.created_at == ctx.last_updated
    
    def test_context_serialization(self):
        """WorkflowContext serializes/deserializes correctly."""
        ctx = WorkflowContext()
        ctx.set("test_data", {"key": "value"})
        ctx.update_metadata(workflow_name="test_workflow")
        
        # Serialize to dictionary
        serialized = ctx.to_dict()
        
        # Verify serialized structure
        assert "data" in serialized
        assert "metadata" in serialized
        assert "created_at" in serialized
        assert "last_updated" in serialized
        
        # Deserialize and verify
        restored = WorkflowContext.from_dict(serialized)
        
        assert restored.get("test_data") == {"key": "value"}
        assert restored.metadata.get("workflow_name") == "test_workflow"
        assert restored.created_at == ctx.created_at
        assert restored.last_updated == ctx.last_updated
    
    def test_data_management(self):
        """Test data setting, getting, and removal."""
        ctx = WorkflowContext()
        
        # Test setting and getting data
        ctx.set("key1", "value1")
        ctx.set("key2", {"nested": "data"})
        
        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == {"nested": "data"}
        assert ctx.get("nonexistent") is None
        assert ctx.get("nonexistent", "default") == "default"
        
        # Test has method
        assert ctx.has("key1") is True
        assert ctx.has("nonexistent") is False
        
        # Test removal
        removed = ctx.remove("key1")
        assert removed == "value1"
        assert ctx.has("key1") is False
        assert ctx.remove("nonexistent") is None
    
    def test_metadata_management(self):
        """Test metadata updates."""
        ctx = WorkflowContext()
        
        # Update metadata
        ctx.update_metadata(step="test_step", status="running")
        
        assert ctx.metadata["step"] == "test_step"
        assert ctx.metadata["status"] == "running"
        
        # Update with more metadata
        ctx.update_metadata(progress=0.5, duration=10.5)
        
        assert ctx.metadata["progress"] == 0.5
        assert ctx.metadata["duration"] == 10.5
        assert ctx.metadata["step"] == "test_step"  # Previous value preserved
    
    def test_timestamp_updates(self):
        """Test that timestamps update correctly."""
        ctx = WorkflowContext()
        initial_time = ctx.last_updated
        
        # Small delay to ensure time difference
        time.sleep(0.01)
        
        # Setting data should update timestamp
        ctx.set("test", "value")
        assert ctx.last_updated > initial_time
        
        updated_time = ctx.last_updated
        time.sleep(0.01)
        
        # Updating metadata should update timestamp
        ctx.update_metadata(test="meta")
        assert ctx.last_updated > updated_time
        
        removal_time = ctx.last_updated
        time.sleep(0.01)
        
        # Removing data should update timestamp
        ctx.remove("test")
        assert ctx.last_updated > removal_time
    
    def test_serialization_safety(self):
        """Test that complex objects are made serializable."""
        ctx = WorkflowContext()
        
        # Test with various data types
        test_data = {
            "string": "value",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": True},
            "bool": True,
            "none": None,
        }
        
        for key, value in test_data.items():
            ctx.set(key, value)
        
        # Serialize and deserialize
        serialized = ctx.to_dict()
        restored = WorkflowContext.from_dict(serialized)
        
        for key, expected_value in test_data.items():
            assert restored.get(key) == expected_value
    
    def test_pickle_compatibility(self):
        """Test that WorkflowContext can be pickled/unpickled."""
        import pickle
        
        ctx = WorkflowContext()
        ctx.set("data", {"test": "value"})
        ctx.update_metadata(workflow="test")
        
        # Pickle and unpickle
        pickled = pickle.dumps(ctx)
        unpickled = pickle.loads(pickled)
        
        # Verify data integrity
        assert unpickled.get("data") == {"test": "value"}
        assert unpickled.metadata["workflow"] == "test"
        assert unpickled.created_at == ctx.created_at
        assert unpickled.last_updated == ctx.last_updated
    
    def test_empty_context_serialization(self):
        """Test serialization of empty context."""
        ctx = WorkflowContext()
        
        serialized = ctx.to_dict()
        restored = WorkflowContext.from_dict(serialized)
        
        assert restored.data == {}
        assert restored.metadata == {}
        assert restored.created_at is not None
        assert restored.last_updated is not None
    
    def test_context_with_custom_timestamps(self):
        """Test context with custom timestamps."""
        custom_time = 1234567890.0
        
        ctx = WorkflowContext(
            data={"test": "data"},
            metadata={"test": "meta"},
            created_at=custom_time,
            last_updated=custom_time
        )
        
        assert ctx.created_at == custom_time
        assert ctx.last_updated == custom_time
        
        # Serialize and restore
        serialized = ctx.to_dict()
        restored = WorkflowContext.from_dict(serialized)
        
        assert restored.created_at == custom_time
        assert restored.last_updated == custom_time
    
    def test_malformed_deserialization(self):
        """Test deserialization with missing or invalid data."""
        # Test with missing fields
        incomplete_data = {"data": {"test": "value"}}
        ctx = WorkflowContext.from_dict(incomplete_data)
        
        assert ctx.get("test") == "value"
        assert ctx.metadata == {}
        assert ctx.created_at is None
        assert ctx.last_updated is None
        
        # Test with completely empty dict
        empty_ctx = WorkflowContext.from_dict({})
        
        assert empty_ctx.data == {}
        assert empty_ctx.metadata == {}
        assert empty_ctx.created_at is None
        assert empty_ctx.last_updated is None