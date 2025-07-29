#!/bin/bash

# Backend API Startup Script
# This script starts the Flask REST API backend server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Linux Patching Automation Backend API...${NC}"

# Check if we're in the correct directory
if [ ! -f "backend_api/app.py" ]; then
    echo -e "${RED}Error: backend_api/app.py not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set environment variables
export FLASK_APP=backend_api/app.py
export FLASK_ENV=development
export API_PORT=8000

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r backend_api/requirements.txt

# Check if main requirements are also needed
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Start the API server
echo -e "${GREEN}Starting API server on port ${API_PORT}...${NC}"
echo -e "${YELLOW}API will be available at: http://localhost:${API_PORT}/api${NC}"
echo -e "${YELLOW}Health check: http://localhost:${API_PORT}/api/health${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the server
cd backend_api
python app.py