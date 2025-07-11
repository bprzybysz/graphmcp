"""
GraphMCP UI Demo

This script launches the new Streamlit-based UI for the GraphMCP workflow orchestrator.
To run the UI, execute this script from your terminal:

    python ui_demo.py
"""

import os
import sys

# Ensure the package root is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from ui.app import main

if __name__ == "__main__":
    # The main function in app.py handles page setup and layout rendering.
    main()
