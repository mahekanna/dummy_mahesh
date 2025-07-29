# Complete Linux Patching Automation Solution

## Overview

This is a complete, production-ready Linux patching automation solution that combines:

- **Modern React Frontend** (TypeScript + Material-UI)
- **REST API Backend** (Flask + JWT authentication)
- **Existing Python CLI System** (7-step workflow automation)
- **WebSocket Real-time Updates**
- **Comprehensive Security** (JWT tokens, role-based access, audit logging)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     COMPLETE SOLUTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐ │
│  │   React Frontend│◄──►│   REST API      │◄──►│   Python CLI│ │
│  │   Port 3000     │    │   Port 8001     │    │   Existing  │ │
│  │                 │    │                 │    │   System    │ │
│  │ • TypeScript    │    │ • Flask         │    │ • 7-step    │ │
│  │ • Material-UI   │    │ • JWT Auth      │    │   workflow  │ │
│  │ • WebSocket     │    │ • WebSocket     │    │ • Email     │ │
│  │ • Real-time     │    │ • CORS enabled  │    │ • CSV data  │ │
│  │ • Responsive    │    │ • Rate limiting │    │ • SSH ops   │ │
│  └─────────────────┘    └─────────────────┘    └─────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Features

### ✅ React Frontend
- **Modern UI**: TypeScript + Material-UI components
- **Authentication**: JWT-based login with role management
- **Dashboard**: Real-time system overview and metrics
- **Server Management**: Complete CRUD operations
- **Patching Jobs**: Interactive job management with progress tracking
- **Approvals**: Workflow-based approval system
- **Reports**: Generate and download comprehensive reports
- **Real-time Updates**: WebSocket-powered live updates
- **Responsive Design**: Mobile-friendly interface

### ✅ REST API Backend
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin, Operator, and Viewer roles
- **Complete CRUD**: Full server management capabilities
- **Patching Workflow**: Start, monitor, and control patching jobs
- **Approval System**: Create, approve, and reject patching requests
- **Pre-check System**: Run and monitor pre-patching validations
- **Reporting**: Generate various report formats (CSV, JSON)
- **System Health**: Comprehensive health monitoring
- **Audit Logging**: Complete activity tracking
- **WebSocket Support**: Real-time job updates and notifications
- **Rate Limiting**: API protection against abuse
- **CORS Support**: Cross-origin resource sharing

### ✅ Python CLI Integration
- **7-step Workflow**: Complete automation pipeline
- **Email System**: HTML email templates and notifications
- **CSV Data Management**: Intelligent field mapping and validation
- **SSH Operations**: Remote server management
- **Timezone Handling**: Global timezone support
- **Custom Quarters**: Q1 (Nov-Jan), Q2 (Feb-Apr), Q3 (May-Jul), Q4 (Aug-Oct)
- **LDAP Integration**: Enterprise authentication
- **Intelligent Scheduling**: AI-powered scheduling recommendations

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Git

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd linux_patching_automation
   ```

2. **Start Complete Solution**
   ```bash
   ./start_complete_solution.sh
   ```

3. **Access the Application**
   - Frontend: http://localhost:3000
   - API Backend: http://localhost:8001
   - WebSocket: ws://localhost:8001/ws

### Default Login
- Username: `admin@company.com`
- Password: `admin123`

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - User logout  
- `GET /auth/profile` - Get user profile

### Server Management
- `GET /servers` - List servers (paginated, filtered)
- `POST /servers` - Create server
- `GET /servers/{id}` - Get server details
- `PUT /servers/{id}` - Update server
- `DELETE /servers/{id}` - Delete server
- `POST /servers/{id}/test` - Test connectivity
- `POST /servers/import` - Import CSV
- `GET /servers/export` - Export CSV

### Patching Operations
- `GET /patching/status` - Get patching status
- `POST /patching/start` - Start patching job
- `GET /patching/jobs` - List patching jobs
- `GET /patching/jobs/{id}` - Get job details
- `POST /patching/jobs/{id}/cancel` - Cancel job
- `POST /patching/rollback` - Rollback server

### Pre-checks
- `POST /precheck/run` - Run pre-checks
- `GET /precheck/results` - Get pre-check results

### Approvals
- `GET /approvals` - List approval requests
- `POST /approvals` - Create approval request
- `POST /approvals/approve` - Approve servers
- `POST /approvals/reject` - Reject servers

### Reports
- `POST /reports/generate` - Generate report
- `GET /reports/{id}` - Download report
- `POST /reports/{id}/email` - Email report

### System
- `GET /system/health` - System health check
- `GET /system/stats` - System statistics
- `POST /system/test-email` - Test email config
- `GET /audit/logs` - Audit logs

## Configuration

### Environment Variables
```bash
# API Backend
export JWT_SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"

# React Frontend
export REACT_APP_API_URL="http://localhost:8001"
export REACT_APP_WS_URL="ws://localhost:8001"
```

### Settings
Main configuration is in `config/settings.py`:
- Database connections
- Email configuration
- LDAP settings
- Custom quarters
- File paths

## Security Features

### Multi-layer Security
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin, Operator, Viewer roles
- **Input Validation**: Comprehensive validation and sanitization
- **Rate Limiting**: API protection against abuse
- **CORS Protection**: Cross-origin request security
- **Audit Logging**: Complete activity tracking
- **Token Blacklisting**: Secure logout implementation

### User Roles
- **Admin**: Full system access and configuration
- **Operator**: Server management and patching operations
- **Viewer**: Read-only access to dashboards and reports

## Development

### Backend Development
```bash
# Start API backend only
cd api_backend
python complete_api.py

# Install dependencies
pip install -r requirements.txt
pip install -r api_backend/requirements.txt
```

### Frontend Development
```bash
# Start React frontend only
cd frontend
npm start

# Install dependencies
npm install
```

### Testing
```bash
# Test API endpoints
curl -X GET http://localhost:8001/health

# Test with authentication
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@company.com", "password": "admin123"}'
```

## Monitoring

### System Health
- Database connectivity
- Email system status
- Storage availability
- Memory and CPU usage
- Active connections

### Metrics
- Total servers managed
- Active patching jobs
- Success/failure rates
- User activity
- System performance

### Logging
- Application logs: `logs/`
- API request logs
- Audit trail
- Error tracking

## Deployment

### Production Setup
1. Set secure JWT secret key
2. Configure production database
3. Set up SMTP for emails
4. Configure LDAP authentication
5. Set up SSL/TLS certificates
6. Configure firewall rules
7. Set up monitoring and alerting

### Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d
```

### Systemd Service
```bash
# Install as systemd service
sudo cp scripts/patching-api.service /etc/systemd/system/
sudo systemctl enable patching-api
sudo systemctl start patching-api
```

## Maintenance

### Regular Tasks
- **Daily**: Health checks, log review
- **Weekly**: Security updates, performance monitoring
- **Monthly**: System updates, user access review
- **Quarterly**: Major updates, security audits

### Backup
- Server data (CSV files)
- Configuration files
- Log files
- User data

### Updates
```bash
# Stop services
./start_complete_solution.sh --stop

# Update code
git pull origin main

# Restart services
./start_complete_solution.sh
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -tuln | grep :8001
   
   # Kill process
   sudo kill -9 $(lsof -t -i:8001)
   ```

2. **JWT Token Issues**
   ```bash
   # Check token expiration
   # Tokens expire after 8 hours by default
   ```

3. **Database Connection**
   ```bash
   # Check CSV file permissions
   ls -la data/servers.csv
   ```

4. **Email Configuration**
   ```bash
   # Test email settings
   curl -X POST http://localhost:8001/system/test-email \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"recipient": "test@company.com"}'
   ```

### Logs
- API Backend: Check console output
- React Frontend: Check browser console
- System logs: `logs/` directory

## Support

### Getting Help
1. Check the logs for error messages
2. Review the troubleshooting section
3. Check the API documentation
4. Review the system health endpoint

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built on existing Linux patching automation system
- Integrates with Flask, React, and Python CLI components
- Uses Material-UI for modern interface design
- Implements JWT authentication for security
- Provides WebSocket real-time updates

---

**The complete solution is now ready for production use with modern React frontend, secure REST API backend, and full integration with the existing Python CLI system.**