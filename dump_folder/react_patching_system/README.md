# React Patching System

A modern React-based frontend with REST API backend for Linux Patching Automation, converted from the original Flask web portal.

## Project Structure

```
react_patching_system/
├── backend/                 # REST API Backend (Flask)
│   ├── app.py              # Main API server
│   ├── routes/             # API route modules
│   │   ├── admin.py        # Admin functionality
│   │   ├── reports.py      # Reports and analytics
│   │   └── utils.py        # Utility endpoints
│   └── requirements.txt    # Backend dependencies
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Main pages
│   │   ├── services/       # API service layer
│   │   ├── contexts/       # React contexts
│   │   └── App.tsx         # Main app component
│   ├── package.json        # Frontend dependencies
│   └── tsconfig.json       # TypeScript configuration
├── start_system.sh         # System startup script
└── README.md              # This file
```

## Features

### ✅ Complete Feature Conversion
- **Authentication**: JWT-based login with LDAP integration
- **Dashboard**: Server overview with patching schedules and statuses
- **Server Management**: Individual server detail pages with scheduling
- **Admin Panel**: System administration and configuration
- **Reports**: Interactive reports dashboard with CSV export
- **AI Recommendations**: Smart scheduling based on load patterns
- **Real-time Updates**: Live system status and notifications

### ✅ Modern React Architecture
- **TypeScript**: Full type safety and IntelliSense
- **Material-UI**: Modern, responsive component library
- **Context API**: State management for auth and notifications
- **React Router**: Client-side routing
- **Axios**: HTTP client with interceptors
- **Error Boundaries**: Graceful error handling

### ✅ REST API Backend
- **Flask**: Lightweight Python web framework
- **JWT Authentication**: Secure token-based authentication
- **CORS Support**: Cross-origin resource sharing
- **Blueprint Architecture**: Modular route organization
- **Error Handling**: Comprehensive error responses
- **Health Checks**: System monitoring endpoints

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Linux Patching Automation system (parent directory)

### Installation & Startup

1. **Clone and navigate to the project**
   ```bash
   cd /home/vijji/linux_patching_automation/react_patching_system
   ```

2. **Start the complete system**
   ```bash
   ./start_system.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8002
   - API Health: http://localhost:8002/api/health

### Demo Login Credentials
- Username: `patchadmin`
- Password: `admin123`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile

### Server Management
- `GET /api/servers` - List servers (filtered by user permissions)
- `GET /api/servers/{name}` - Get server details
- `PUT /api/servers/{name}/schedule` - Update server schedule
- `POST /api/servers/{name}/approve` - Approve server schedule
- `PUT /api/servers/{name}/info` - Update server info (admin only)

### Utility Endpoints
- `GET /api/utils/available-dates/{quarter}` - Get available patch dates
- `GET /api/utils/server-timezone/{name}` - Get server timezone info
- `GET /api/utils/ai-recommendation/{name}/{quarter}` - Get AI recommendations
- `GET /api/utils/system/health` - System health check
- `GET /api/utils/system/stats` - System statistics

### Admin Endpoints (Admin Only)
- `POST /api/admin/reports/generate/{type}` - Generate reports
- `POST /api/admin/database/sync` - Sync database
- `POST /api/admin/scheduling/intelligent` - Run intelligent scheduling

### Reports
- `GET /api/reports/dashboard` - Reports dashboard data
- `GET /api/reports/csv` - Export CSV reports

## Development

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Frontend Development
```bash
cd frontend
npm install
npm start
```

## Key Conversions from Flask

### Authentication
- **Flask**: Session-based authentication with Flask-Login
- **React**: JWT tokens stored in localStorage with Context API

### Templates → Components
- **Flask**: Jinja2 templates (base.html, dashboard.html, etc.)
- **React**: TypeScript components with Material-UI styling

### Forms → State Management
- **Flask**: Server-side form processing
- **React**: Client-side form state with controlled components

### Flash Messages → Notifications
- **Flask**: Server-side flash messages
- **React**: Toast notifications with Context API

### Server-Side Rendering → Client-Side Routing
- **Flask**: Server renders HTML pages
- **React**: Single-page application with React Router

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: Admin, User, and Read-only roles
- **Input Validation**: Client and server-side validation
- **CORS Protection**: Configured for secure cross-origin requests
- **Token Expiration**: 8-hour token lifetime with automatic refresh

## User Roles

- **Admin**: Full system access, can modify all servers and settings
- **User**: Can modify servers they own (primary/secondary owner)
- **Read-only**: View-only access to assigned servers

## Custom Quarter System

The system uses a custom quarter definition:
- **Q1**: November to January
- **Q2**: February to April
- **Q3**: May to July
- **Q4**: August to October

## Integration with Existing System

The React system integrates with the existing Linux Patching Automation:
- **CSV Data**: Reads from existing `data/servers.csv`
- **User Management**: Uses existing `config/users.py`
- **Email System**: Uses existing `utils/email_sender.py`
- **Timezone Handling**: Uses existing `utils/timezone_handler.py`
- **Configuration**: Uses existing `config/settings.py`

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   netstat -tuln | grep :8002
   netstat -tuln | grep :3000
   
   # Kill processes if needed
   kill -9 $(lsof -t -i:8002)
   kill -9 $(lsof -t -i:3000)
   ```

2. **Backend Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

4. **Permission Issues**
   - Ensure the script has execute permissions: `chmod +x start_system.sh`
   - Check that the parent directory CSV files are readable

### Health Checks
- Backend: http://localhost:8002/api/health
- Frontend: Check browser console for errors
- System: Check terminal output for error messages

## Future Enhancements

- **WebSocket**: Real-time updates for patching progress
- **Push Notifications**: Browser notifications for important events
- **Mobile Responsiveness**: Enhanced mobile interface
- **Dark Mode**: Theme switching capability
- **Advanced Charts**: More detailed analytics visualizations
- **Bulk Operations**: Multi-server management capabilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the Linux Patching Automation System and follows the same license terms.

---

**Successfully converted from Flask web portal to modern React application with full feature parity and enhanced user experience.**