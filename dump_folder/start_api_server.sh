#!/bin/bash

# API Server Startup Script
# Start just the REST API backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting REST API Server...${NC}"

# Check if we're in the correct directory
if [ ! -f "api_server/app.py" ]; then
    echo -e "${RED}Error: api_server/app.py not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r api_server/requirements.txt

# Install main project dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Set environment variables
export FLASK_ENV=development
export JWT_SECRET_KEY=your-secret-key-change-in-production
export API_PORT=8000

# Start the API server
echo -e "${GREEN}Starting API server on port 8000...${NC}"
echo -e "${YELLOW}API will be available at: http://localhost:8000${NC}"
echo -e "${YELLOW}Health check: http://localhost:8000/api/health${NC}"
echo -e "${YELLOW}CORS enabled for: http://localhost:3000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

cd api_server
python app.py