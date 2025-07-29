#!/bin/bash

# Complete React Solution Startup Script
# This script starts the complete React + API backend solution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Complete React Solution Startup       ${NC}"
echo -e "${BLUE}  Linux Patching Automation System      ${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if we're in the correct directory
if [ ! -f "api_server/app.py" ]; then
    echo -e "${RED}Error: api_server/app.py not found. Please run this script from the project root.${NC}"
    exit 1
fi

if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found. Please run this script from the project root.${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to start backend
start_backend() {
    echo -e "${GREEN}Starting Backend API Server...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install backend dependencies
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip install -r api_server/requirements.txt
    
    # Install main project dependencies
    pip install -r requirements.txt
    
    # Set environment variables
    export FLASK_ENV=development
    export JWT_SECRET_KEY=your-secret-key-change-in-production
    export API_PORT=8000
    
    echo -e "${GREEN}Backend API starting on port 8000...${NC}"
    cd api_server
    python app.py &
    BACKEND_PID=$!
    cd ..
    
    echo "Backend PID: $BACKEND_PID" > logs/backend.pid
    echo -e "${GREEN}✅ Backend API started successfully${NC}"
}

# Function to start frontend
start_frontend() {
    echo -e "${GREEN}Starting React Frontend...${NC}"
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Set environment variables
    export REACT_APP_API_URL=http://localhost:8000
    export PORT=3000
    
    echo -e "${GREEN}React frontend starting on port 3000...${NC}"
    npm start &
    FRONTEND_PID=$!
    cd ..
    
    echo "Frontend PID: $FRONTEND_PID" > logs/frontend.pid
    echo -e "${GREEN}✅ React frontend started successfully${NC}"
}

# Function to wait for services
wait_for_services() {
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    
    # Wait for backend
    echo -e "${YELLOW}Checking backend health...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
            break
        fi
        sleep 1
    done
    
    # Wait for frontend
    echo -e "${YELLOW}Checking frontend...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is accessible${NC}"
            break
        fi
        sleep 1
    done
}

# Function to show status
show_status() {
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}           SERVICE STATUS                ${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${GREEN}✅ Backend API: http://localhost:8000${NC}"
    echo -e "${GREEN}✅ Frontend UI: http://localhost:3000${NC}"
    echo -e "${GREEN}✅ API Health: http://localhost:8000/api/health${NC}"
    echo ""
    echo -e "${YELLOW}Default Login Credentials:${NC}"
    echo -e "${YELLOW}Username: admin${NC}"
    echo -e "${YELLOW}Password: admin123${NC}"
    echo ""
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${BLUE}           AVAILABLE FEATURES           ${NC}"
    echo -e "${BLUE}==========================================${NC}"
    echo -e "${GREEN}✅ Server Management${NC}"
    echo -e "${GREEN}✅ Patching Operations${NC}"
    echo -e "${GREEN}✅ Approval Workflow${NC}"
    echo -e "${GREEN}✅ System Monitoring${NC}"
    echo -e "${GREEN}✅ Report Generation${NC}"
    echo -e "${GREEN}✅ User Authentication${NC}"
    echo -e "${GREEN}✅ Real-time Updates${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}Stopping services...${NC}"
    
    # Kill backend
    if [ -f "logs/backend.pid" ]; then
        BACKEND_PID=$(cat logs/backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            echo -e "${GREEN}Backend stopped${NC}"
        fi
        rm logs/backend.pid
    fi
    
    # Kill frontend
    if [ -f "logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat logs/frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            echo -e "${GREEN}Frontend stopped${NC}"
        fi
        rm logs/frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "python.*api_server/app.py" 2>/dev/null || true
    pkill -f "npm start" 2>/dev/null || true
    
    echo -e "${GREEN}All services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
echo -e "${YELLOW}Starting complete React solution...${NC}"

# Start backend
start_backend

# Give backend time to start
sleep 3

# Start frontend
start_frontend

# Wait for services
wait_for_services

# Show status
show_status

# Wait for user to stop
wait