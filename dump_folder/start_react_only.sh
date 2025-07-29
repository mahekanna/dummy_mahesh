#!/bin/bash

# React Frontend Startup Script
# Start just the React frontend (API server must be running separately)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting React Frontend...${NC}"

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
    echo -e "${YELLOW}Dependencies already installed${NC}"
fi

# Update package.json proxy if needed
if ! grep -q '"proxy"' package.json; then
    echo -e "${YELLOW}Adding proxy configuration...${NC}"
    # Add proxy configuration
    sed -i 's/"private": true,/"private": true,\n  "proxy": "http:\/\/localhost:8000",/' package.json
fi

# Start the React development server
echo -e "${GREEN}Starting React development server on port 3000...${NC}"
echo -e "${YELLOW}Frontend will be available at: http://localhost:3000${NC}"
echo -e "${YELLOW}Make sure the API server is running on port 8000${NC}"
echo -e "${YELLOW}API Health Check: http://localhost:8000/api/health${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Start the server
npm start