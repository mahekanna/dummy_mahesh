#!/bin/bash

# Simple startup script - no complex dependencies

echo "Starting Simple API Backend..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Install minimal requirements
echo "Installing minimal requirements..."
pip3 install --user flask flask-cors pyjwt

# Start the API
echo "Starting API on port 8001..."
python3 simple_api.py