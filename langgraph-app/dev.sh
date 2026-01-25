#!/bin/bash
# LangGraph Development Server Startup Script
# Sets up environment and starts dev server with correct PYTHONPATH

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set PYTHONPATH to include src directory
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(pwd)/src"

echo "Starting LangGraph dev server..."
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# Start langgraph dev server
langgraph dev
