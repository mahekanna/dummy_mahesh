#!/bin/bash

# React Patching System - Startup Script
# Starts both backend API and React frontend

set -e

PROJECT_DIR="/home/vijji/linux_patching_automation/react_patching_system"
BACKEND_DIR="${PROJECT_DIR}/backend"
FRONTEND_DIR="${PROJECT_DIR}/frontend"

echo "🚀 Starting React Patching System..."

# Function to check if port is available
check_port() {
    local port=$1
    if netstat -tuln | grep -q ":${port} "; then
        echo "❌ Port ${port} is already in use"
        return 1
    fi
    return 0
}

# Check required ports
echo "🔍 Checking required ports..."
check_port 8002 || { echo "Backend port 8002 is in use. Please free it or change the port."; exit 1; }
check_port 3000 || { echo "Frontend port 3000 is in use. Please free it or change the port."; exit 1; }

# Start backend API
echo "🔧 Starting Backend API..."
cd "$BACKEND_DIR"

# Install backend dependencies if not already installed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Installing backend dependencies..."
pip install -r requirements.txt

echo "🔧 Starting Backend API on port 8002..."
python app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 5

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend API started successfully (PID: $BACKEND_PID)"
else
    echo "❌ Backend API failed to start"
    exit 1
fi

# Start frontend
echo "🎨 Starting React Frontend..."
cd "$FRONTEND_DIR"

# Install frontend dependencies if not already installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo "🎨 Starting React Frontend on port 3000..."
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
sleep 10

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null; then
    echo "✅ React Frontend started successfully (PID: $FRONTEND_PID)"
else
    echo "❌ React Frontend failed to start"
    kill $BACKEND_PID
    exit 1
fi

echo ""
echo "🎉 React Patching System started successfully!"
echo ""
echo "📊 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8002"
echo "   API Health: http://localhost:8002/api/health"
echo ""
echo "👤 Demo Login Credentials:"
echo "   Username: patchadmin"
echo "   Password: admin123"
echo ""
echo "🔧 System Information:"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "⚠️  To stop the system:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or use Ctrl+C to stop this script"
echo ""

# Keep script running and handle cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping React Patching System..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "✅ System stopped"
    exit 0
}

trap cleanup INT TERM

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID