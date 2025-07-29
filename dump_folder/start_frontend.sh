#!/bin/bash

# Frontend Startup Script
# This script starts the React development server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Linux Patching Automation Frontend...${NC}"

# Check if we're in the correct directory
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found in frontend directory.${NC}"
    exit 1
fi

# Set environment variables
export REACT_APP_API_URL=http://localhost:8000
export PORT=3000

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
else
    echo -e "${YELLOW}Dependencies already installed, checking for updates...${NC}"
    npm install
fi

# Start the React development server
echo -e "${GREEN}Starting React development server on port ${PORT}...${NC}"
echo -e "${YELLOW}Frontend will be available at: http://localhost:${PORT}${NC}"
echo -e "${YELLOW}Make sure the backend API is running on port 8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the server
npm start