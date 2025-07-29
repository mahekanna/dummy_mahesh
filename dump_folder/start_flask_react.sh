#!/bin/bash

# Start Flask app with React integration
cd /home/vijji/linux_patching_automation/web_portal

echo "🚀 Starting Flask + React application..."
echo "📊 Access URL: http://localhost:5000"
echo "👤 Login with your existing credentials"
echo ""

# Set Flask environment
export FLASK_APP=app.py
export FLASK_ENV=development

# Start Flask
python3 app.py
