# React Migration Guide

## Overview

This guide covers the complete migration from the Flask web portal to a modern React + REST API architecture for the Linux Patching Automation system.

## Architecture Changes

### Before (Flask Web Portal)
- **Frontend**: Server-side rendered HTML templates
- **Backend**: Flask app with HTML responses
- **Authentication**: Session-based with Flask-Login
- **API**: Limited API endpoints, mostly HTML responses

### After (React + REST API)
- **Frontend**: React SPA with TypeScript
- **Backend**: Flask REST API with JSON responses
- **Authentication**: JWT-based authentication
- **API**: Complete REST API with proper endpoints

## Project Structure

```
linux_patching_automation/
├── backend_api/                    # New Flask REST API
│   ├── app.py                     # Main Flask application
│   ├── config.py                  # Configuration settings
│   ├── requirements.txt           # Python dependencies
│   ├── routes/                    # API routes
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication endpoints
│   │   ├── servers.py            # Server management
│   │   ├── patching.py           # Patching operations
│   │   ├── approvals.py          # Approval management
│   │   ├── reports.py            # Report generation
│   │   ├── system.py             # System health/stats
│   │   ├── audit.py              # Audit logs
│   │   └── health.py             # Health checks
│   ├── utils/                     # Utility modules
│   │   ├── audit.py              # Audit logging
│   │   ├── pagination.py         # Pagination helpers
│   │   └── validators.py         # Data validation
│   ├── decorators.py             # Permission decorators
│   ├── middleware.py             # Request/response middleware
│   └── error_handlers.py         # Error handling
├── frontend/                      # React application
│   ├── public/                   # Static assets
│   ├── src/                      # React source code
│   │   ├── components/           # Reusable components
│   │   ├── pages/                # Page components
│   │   ├── services/             # API services
│   │   ├── types/                # TypeScript types
│   │   ├── utils/                # Utility functions
│   │   ├── hooks/                # Custom React hooks
│   │   ├── store/                # State management
│   │   └── constants/            # Constants
│   ├── package.json              # Node.js dependencies
│   └── tsconfig.json             # TypeScript configuration
├── start_backend.sh              # Backend startup script
├── start_frontend.sh             # Frontend startup script
└── web_portal/                   # Legacy Flask web portal
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password

### Servers
- `GET /api/servers` - Get all servers (with pagination)
- `GET /api/servers/{id}` - Get specific server
- `POST /api/servers` - Create new server
- `PUT /api/servers/{id}` - Update server
- `DELETE /api/servers/{id}` - Delete server
- `POST /api/servers/{id}/test` - Test server connectivity

### Patching
- `GET /api/patching/status` - Get patching status
- `POST /api/patching/start` - Start patching job
- `GET /api/patching/jobs` - Get patching jobs
- `GET /api/patching/jobs/{id}` - Get specific job
- `POST /api/patching/jobs/{id}/cancel` - Cancel job
- `POST /api/patching/rollback` - Rollback server

### Approvals
- `GET /api/approvals` - Get approval requests
- `POST /api/approvals` - Create approval request
- `POST /api/approvals/approve` - Approve servers
- `POST /api/approvals/reject` - Reject servers

### Reports
- `POST /api/reports/generate` - Generate report
- `GET /api/reports/{id}` - Get report status
- `GET /api/reports/{id}/download` - Download report
- `POST /api/reports/{id}/email` - Email report

### System
- `GET /api/system/health` - System health check
- `GET /api/system/stats` - System statistics
- `POST /api/system/test-email` - Test email configuration

### Audit
- `GET /api/audit/logs` - Get audit logs

### Health
- `GET /api/health` - Basic health check
- `GET /api/health/ready` - Readiness check
- `GET /api/health/live` - Liveness check

## Quick Start

### 1. Start Backend API

```bash
# From project root
./start_backend.sh
```

This will:
- Create virtual environment if needed
- Install Python dependencies
- Start Flask API on port 8000

### 2. Start Frontend

```bash
# From project root (in new terminal)
./start_frontend.sh
```

This will:
- Install Node.js dependencies
- Start React development server on port 3000

### 3. Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **API Health**: http://localhost:8000/api/health

## Configuration

### Backend Configuration

Edit `backend_api/config.py` or set environment variables:

```bash
# Database
DATABASE_URL=sqlite:///patching.db

# JWT
JWT_SECRET_KEY=your-secret-key-here

# CORS
CORS_ORIGINS=http://localhost:3000

# Email
SMTP_SERVER=your-smtp-server
SMTP_PORT=587
EMAIL_FROM=patching@company.com

# API Port
API_PORT=8000
```

### Frontend Configuration

Edit environment variables in `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
PORT=3000
```

## Authentication

### JWT Token Flow

1. User logs in via `/api/auth/login`
2. Backend returns access token and refresh token
3. Frontend stores tokens in localStorage
4. All API requests include `Authorization: Bearer <token>` header
5. When token expires, use refresh token to get new access token

### Permissions

Users have roles (admin, operator, viewer) and specific permissions:

- **Admin**: Full access to all features
- **Operator**: Can manage servers and patching
- **Viewer**: Read-only access

## Data Flow

### Server Management
1. Frontend calls `/api/servers` to get server list
2. Backend reads from CSV file and returns JSON
3. Frontend displays servers in DataGrid
4. CRUD operations update CSV file via API

### Patching Operations
1. Frontend creates patching job via `/api/patching/start`
2. Backend creates job and returns job ID
3. Frontend polls `/api/patching/jobs/{id}` for status
4. Real-time updates via WebSocket (future enhancement)

## Migration Steps

### Phase 1: Backend API (Completed)
- ✅ Created Flask REST API structure
- ✅ Implemented JWT authentication
- ✅ Created all required endpoints
- ✅ Added error handling and validation
- ✅ Implemented audit logging

### Phase 2: Frontend Integration (Ready)
- ✅ React app structure exists
- ✅ API service layer implemented
- ✅ TypeScript types defined
- ✅ Components created

### Phase 3: Testing & Production
- [ ] Unit tests for backend API
- [ ] Integration tests
- [ ] Production deployment configuration
- [ ] Database migration (if needed)

## Development

### Backend Development

```bash
# Install dependencies
pip install -r backend_api/requirements.txt

# Run tests
pytest backend_api/tests/

# Run with debug mode
export FLASK_ENV=development
python backend_api/app.py
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Run tests
npm test

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
```

## Testing

### Backend Testing

```bash
# Run all tests
pytest backend_api/tests/

# Run with coverage
pytest --cov=backend_api backend_api/tests/

# Test specific module
pytest backend_api/tests/test_auth.py
```

### Frontend Testing

```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run test:e2e

# Run accessibility tests
npm run accessibility
```

## Deployment

### Production Environment

1. **Backend Deployment**:
   - Use production WSGI server (Gunicorn)
   - Set `FLASK_ENV=production`
   - Configure proper database
   - Set up logging

2. **Frontend Deployment**:
   - Build React app: `npm run build`
   - Serve static files via nginx
   - Configure proxy to backend API

### Docker Deployment

```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY backend_api/requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "backend_api.app:create_app()", "--bind", "0.0.0.0:8000"]

# Frontend Dockerfile
FROM node:16-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
```

## Security

### Authentication Security
- JWT tokens with expiration
- Refresh token rotation
- Password hashing with bcrypt
- Session management

### API Security
- CORS configuration
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection headers

### Network Security
- HTTPS in production
- Secure headers
- API key authentication (optional)

## Monitoring

### Application Monitoring
- Health check endpoints
- System metrics (CPU, memory, disk)
- API response times
- Error rates

### Audit Logging
- User actions logged
- File-based audit trail
- API request logging
- Security events

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   ```bash
   # Check CORS_ORIGINS in backend config
   export CORS_ORIGINS=http://localhost:3000
   ```

2. **Authentication Issues**:
   ```bash
   # Check JWT secret key
   export JWT_SECRET_KEY=your-secret-key
   ```

3. **Database Connection**:
   ```bash
   # Check database URL
   export DATABASE_URL=sqlite:///patching.db
   ```

4. **Permission Errors**:
   - Check user roles in `config/users.py`
   - Verify permission decorators

### Debug Mode

```bash
# Backend debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Frontend debug mode
export REACT_APP_DEBUG=true
```

## Future Enhancements

### Planned Features
- WebSocket for real-time updates
- Redis for caching and job queue
- PostgreSQL for production database
- Docker container deployment
- Kubernetes orchestration
- Advanced reporting
- Mobile-responsive design
- Dark mode support

### API Improvements
- GraphQL endpoint (optional)
- API versioning
- Rate limiting per user
- Bulk operations
- File upload handling
- Async job processing

## Support

For issues or questions:
- Check logs in `logs/` directory
- Run health checks: `curl http://localhost:8000/api/health`
- Enable debug mode for verbose output
- Review audit logs for security events

## Migration Checklist

- [ ] Backend API running on port 8000
- [ ] Frontend running on port 3000
- [ ] User authentication working
- [ ] Server management functional
- [ ] Patching operations working
- [ ] Reports generation working
- [ ] All existing data migrated
- [ ] Users trained on new interface
- [ ] Old Flask portal disabled
- [ ] Production deployment complete

This migration provides a modern, scalable architecture while maintaining all existing functionality.