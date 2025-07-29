#!/bin/bash

# Complete Linux Patching Automation Solution Startup Script
# This script starts both the React frontend and the REST API backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Linux Patching Automation - Complete Solution${NC}"
    echo -e "${BLUE}================================================${NC}"
}

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}

# Function to check port availability
check_port() {
    local port=$1
    local service=$2
    
    if netstat -tuln | grep -q ":$port "; then
        print_warning "Port $port is already in use. $service may already be running."
        return 1
    fi
    return 0
}

# Function to start backend
start_backend() {
    print_status "Starting REST API Backend..."
    
    cd "$(dirname "$0")"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/upgrade backend dependencies
    print_status "Installing backend dependencies..."
    pip install -r requirements.txt
    pip install -r api_backend/requirements.txt
    
    # Check if data directory exists
    if [ ! -d "data" ]; then
        print_error "Data directory not found. Please ensure servers.csv exists in data/ directory."
        exit 1
    fi
    
    # Check if servers.csv exists
    if [ ! -f "data/servers.csv" ]; then
        print_error "servers.csv not found in data/ directory. Please add server data."
        exit 1
    fi
    
    # Start the API backend
    print_status "Starting API backend on port 8001..."
    cd api_backend
    python complete_api.py &
    BACKEND_PID=$!
    
    # Wait a moment for backend to start
    sleep 3
    
    # Check if backend started successfully
    if ! ps -p $BACKEND_PID > /dev/null; then
        print_error "Failed to start API backend"
        exit 1
    fi
    
    print_status "API backend started successfully (PID: $BACKEND_PID)"
    echo $BACKEND_PID > ../backend.pid
    
    cd ..
}

# Function to start frontend
start_frontend() {
    print_status "Starting React Frontend..."
    
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_status "Installing frontend dependencies..."
        npm install
    fi
    
    # Set environment variables
    export REACT_APP_API_URL=http://localhost:8001
    export REACT_APP_WS_URL=ws://localhost:8001
    
    # Start the React development server
    print_status "Starting React frontend on port 3000..."
    npm start &
    FRONTEND_PID=$!
    
    # Wait a moment for frontend to start
    sleep 5
    
    # Check if frontend started successfully
    if ! ps -p $FRONTEND_PID > /dev/null; then
        print_error "Failed to start React frontend"
        exit 1
    fi
    
    print_status "React frontend started successfully (PID: $FRONTEND_PID)"
    echo $FRONTEND_PID > ../frontend.pid
    
    cd ..
}

# Function to show running services
show_services() {
    print_status "Services Status:"
    echo "  • REST API Backend: http://localhost:8001"
    echo "  • React Frontend: http://localhost:3000"
    echo "  • WebSocket: ws://localhost:8001/ws"
    echo ""
    echo "Available API endpoints:"
    echo "  • Health: GET /health"
    echo "  • Authentication: POST /auth/login"
    echo "  • Servers: GET /servers"
    echo "  • Patching: GET /patching/status"
    echo "  • System Health: GET /system/health"
    echo ""
    echo "Access the application at: http://localhost:3000"
}

# Function to cleanup on exit
cleanup() {
    print_status "Stopping services..."
    
    # Kill backend
    if [ -f backend.pid ]; then
        BACKEND_PID=$(cat backend.pid)
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            print_status "API backend stopped"
        fi
        rm -f backend.pid
    fi
    
    # Kill frontend
    if [ -f frontend.pid ]; then
        FRONTEND_PID=$(cat frontend.pid)
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            print_status "React frontend stopped"
        fi
        rm -f frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "complete_api.py" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    
    print_status "Cleanup completed"
}

# Set up signal handlers
trap cleanup EXIT
trap cleanup SIGINT
trap cleanup SIGTERM

# Main execution
main() {
    print_header
    
    # Check system requirements
    print_status "Checking system requirements..."
    check_command "python3"
    check_command "pip"
    check_command "node"
    check_command "npm"
    
    # Check port availability
    if ! check_port 8001 "API Backend"; then
        print_error "Port 8001 is already in use. Please stop existing services."
        exit 1
    fi
    
    if ! check_port 3000 "React Frontend"; then
        print_error "Port 3000 is already in use. Please stop existing services."
        exit 1
    fi
    
    # Start services
    start_backend
    start_frontend
    
    # Show service information
    show_services
    
    print_status "Complete solution is running!"
    print_status "Press Ctrl+C to stop all services"
    
    # Wait for user to stop services
    while true; do
        sleep 1
        
        # Check if services are still running
        if [ -f backend.pid ]; then
            BACKEND_PID=$(cat backend.pid)
            if ! ps -p $BACKEND_PID > /dev/null; then
                print_error "API backend stopped unexpectedly"
                exit 1
            fi
        fi
        
        if [ -f frontend.pid ]; then
            FRONTEND_PID=$(cat frontend.pid)
            if ! ps -p $FRONTEND_PID > /dev/null; then
                print_error "React frontend stopped unexpectedly"
                exit 1
            fi
        fi
    done
}

# Check if script is run with --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Linux Patching Automation - Complete Solution Startup Script"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --check        Check system requirements only"
    echo "  --stop         Stop running services"
    echo ""
    echo "This script starts both the React frontend and REST API backend."
    echo "The frontend will be available at http://localhost:3000"
    echo "The API backend will be available at http://localhost:8000"
    echo ""
    echo "Press Ctrl+C to stop all services when running."
    exit 0
fi

# Check if script is run with --check
if [ "$1" = "--check" ]; then
    print_header
    print_status "Checking system requirements..."
    
    check_command "python3"
    check_command "pip"
    check_command "node"
    check_command "npm"
    
    print_status "Checking directories..."
    [ -d "frontend" ] || { print_error "Frontend directory not found"; exit 1; }
    [ -d "api_backend" ] || { print_error "API backend directory not found"; exit 1; }
    [ -d "data" ] || { print_error "Data directory not found"; exit 1; }
    [ -f "data/servers.csv" ] || { print_error "servers.csv not found"; exit 1; }
    
    print_status "All requirements satisfied!"
    exit 0
fi

# Check if script is run with --stop
if [ "$1" = "--stop" ]; then
    print_header
    cleanup
    exit 0
fi

# Run main function
main