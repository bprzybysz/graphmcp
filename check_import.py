import sys
import os

print("Current working directory:", os.getcwd())
print("Python path (sys.path):")
for p in sys.path:
    print(f"  - {p}")

try:
    from graphmcp.workflows import WorkflowBuilder
    print("Successfully imported WorkflowBuilder from graphmcp.workflows")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 