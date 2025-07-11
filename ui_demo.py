"""
GraphMCP UI Demo

This script launches the new Streamlit-based UI for the GraphMCP workflow orchestrator.
To run the UI, execute this script from your terminal:

    python ui_demo.py
"""

from don_concrete.ui.app import main

if __name__ == "__main__":
    # The main function in app.py handles page setup and layout rendering.
    main() 