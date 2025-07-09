"""
This module provides utility functions for the GraphMCP framework.
"""

import json

def ensure_serializable(data):
    """
    Ensures data is JSON serializable. A real implementation
    might handle more complex types. This is a placeholder.
    """
    try:
        # A simple check for JSON serializability.
        json.dumps(data, default=str)
        return data
    except (TypeError, ValueError) as e:
        print(f"Warning: object is not fully JSON serializable: {e}")
        return data 