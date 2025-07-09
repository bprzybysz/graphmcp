import os
import sys

# Add the current directory to sys.path to ensure local package discovery
sys.path.insert(0, os.getcwd())

try:
    import graphmcp.workflows
    print('Successfully imported graphmcp.workflows')
except ImportError as e:
    print(f'ImportError: {e}')
except Exception as e:
    print(f'An unexpected error occurred: {e}') 