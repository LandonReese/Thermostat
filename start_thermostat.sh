#!/bin/bash
# Wrapper script to start the thermostat service
# This script automatically detects and uses the virtual environment if it exists

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if venv exists and use it, otherwise use system python3
if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
    PYTHON_CMD="$SCRIPT_DIR/venv/bin/python3"
    echo "Using virtual environment: $PYTHON_CMD"
else
    PYTHON_CMD="python3"
    echo "Virtual environment not found, using system python3: $PYTHON_CMD"
fi

# Run the thermostat control script
exec "$PYTHON_CMD" -u "$SCRIPT_DIR/thermostat_control.py"

