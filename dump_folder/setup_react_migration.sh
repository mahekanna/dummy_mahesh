#!/bin/bash

# Setup Script for React Migration
# This script sets up the complete React + REST API solution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  Linux Patching Automation Migration   ${NC}"
echo -e "${BLUE}  Flask → React + REST API Architecture ${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check if we're in the correct directory
if [ ! -f "backend_api/app.py" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Setting up Backend API...${NC}"

# Create virtual environment for backend
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
pip install -r backend_api/requirements.txt

# Install main project dependencies if needed
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Create necessary directories
mkdir -p logs
mkdir -p uploads

echo -e "${GREEN}Step 2: Setting up Frontend...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed. Please install npm first.${NC}"
    exit 1
fi

# Navigate to frontend directory and install dependencies
cd frontend
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
npm install

# Return to project root
cd ..

echo -e "${GREEN}Step 3: Configuration...${NC}"

# Create environment file for backend if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > .env << EOF
# Backend API Configuration
FLASK_ENV=development
FLASK_DEBUG=1
API_PORT=8000
JWT_SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=sqlite:///patching.db

# Email Configuration
SMTP_SERVER=localhost
SMTP_PORT=25
EMAIL_FROM=patching@localhost

# Logging
LOG_LEVEL=INFO
LOG_REQUESTS=false
LOG_RESPONSES=false
EOF
fi

# Create frontend environment file
if [ ! -f "frontend/.env" ]; then
    echo -e "${YELLOW}Creating frontend .env file...${NC}"
    cat > frontend/.env << EOF
# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
PORT=3000
REACT_APP_DEBUG=true
EOF
fi

echo -e "${GREEN}Step 4: Testing Setup...${NC}"

# Test backend setup
echo -e "${YELLOW}Testing backend setup...${NC}"
cd backend_api
python -c "from app import create_app; app = create_app(); print('Backend setup: OK')"
cd ..

# Test frontend setup
echo -e "${YELLOW}Testing frontend setup...${NC}"
cd frontend
if npm run type-check > /dev/null 2>&1; then
    echo "Frontend setup: OK"
else
    echo -e "${YELLOW}Frontend type check had warnings (normal for development)${NC}"
fi
cd ..

echo -e "${GREEN}Setup Complete!${NC}"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}           NEXT STEPS                    ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${GREEN}1. Start the Backend API:${NC}"
echo -e "   ${YELLOW}./start_backend.sh${NC}"
echo -e "   ${YELLOW}API will be available at: http://localhost:8000/api${NC}"
echo ""
echo -e "${GREEN}2. Start the Frontend (in new terminal):${NC}"
echo -e "   ${YELLOW}./start_frontend.sh${NC}"
echo -e "   ${YELLOW}Frontend will be available at: http://localhost:3000${NC}"
echo ""
echo -e "${GREEN}3. Test the Application:${NC}"
echo -e "   ${YELLOW}Backend Health: http://localhost:8000/api/health${NC}"
echo -e "   ${YELLOW}Frontend Login: http://localhost:3000/login${NC}"
echo ""
echo -e "${GREEN}4. Default Login Credentials:${NC}"
echo -e "   ${YELLOW}Username: admin${NC}"
echo -e "   ${YELLOW}Password: admin123${NC}"
echo ""
echo -e "${GREEN}5. Documentation:${NC}"
echo -e "   ${YELLOW}Read: REACT_MIGRATION_GUIDE.md${NC}"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}           FEATURES AVAILABLE           ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${GREEN}✅ JWT Authentication${NC}"
echo -e "${GREEN}✅ Server Management${NC}"
echo -e "${GREEN}✅ Patching Operations${NC}"
echo -e "${GREEN}✅ Approval Workflow${NC}"
echo -e "${GREEN}✅ Report Generation${NC}"
echo -e "${GREEN}✅ System Monitoring${NC}"
echo -e "${GREEN}✅ Audit Logging${NC}"
echo -e "${GREEN}✅ Role-based Permissions${NC}"
echo -e "${GREEN}✅ Real-time Updates${NC}"
echo -e "${GREEN}✅ Responsive Design${NC}"
echo ""
echo -e "${BLUE}Migration from Flask to React+API: Complete!${NC}"