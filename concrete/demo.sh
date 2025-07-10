#!/bin/bash

# This script demonstrates the GraphMCP Preview workflow streaming functionality
# It will start the MCP Server and the Streamlit UI for live workflow visualization.

# Move to the project root directory (assuming script is in concrete/ subdirectory)
cd "$(dirname "$0")/.."

# Ensure the virtual environment is activated
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run 'make setup' first."
    exit 1
fi

# Set PYTHONPATH to include the current directory for proper module imports
export PYTHONPATH=$PYTHONPATH:$(pwd)

# IMPORTANT: Set your OpenAI API key here if needed for advanced features.
# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key.
# export OPENAI_API_KEY='YOUR_OPENAI_API_KEY'

echo "Starting GraphMCP Preview MCP Server in the background..."
# Start MCP server and redirect its output to a log file
python -m clients.preview_mcp.server > mcp_server.log 2>&1 &
MCP_PID=$!
echo "MCP Server started with PID: $MCP_PID. Log: mcp_server.log"

echo "Waiting a few seconds for server to start..."
sleep 3

echo "Starting Streamlit UI. Open http://localhost:8501 in your browser."
echo "Press Ctrl+C to stop the Streamlit UI. This will also kill the background server."
# Start Streamlit UI in the foreground
streamlit run concrete/preview_ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

echo "Stopping background server..."
kill $MCP_PID 2>/dev/null || true

echo "Demo finished. MCP Server log is in mcp_server.log" 