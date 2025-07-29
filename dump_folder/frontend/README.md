# Linux Patching Automation - Frontend

A modern React-based frontend for the Linux Patching Automation System, built with TypeScript, Material-UI, and comprehensive security features.

## Features

- **Modern React Architecture**: Built with React 18, TypeScript, and Material-UI
- **Security First**: Implements security best practices with vulnerability scanning
- **Comprehensive UI**: Dashboard, server management, patching workflows, and reporting
- **Real-time Updates**: WebSocket integration for live status updates
- **Responsive Design**: Mobile-friendly interface with adaptive layouts
- **Role-based Access**: Permission-based UI elements and routing
- **Type Safety**: Full TypeScript implementation with strict configuration

## Technology Stack

- **Frontend Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **State Management**: TanStack Query (React Query) + Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios with interceptors
- **Form Handling**: React Hook Form with Yup validation
- **Testing**: Jest, React Testing Library, Cypress
- **Build Tool**: Create React App with custom configuration
- **Security**: ESLint security rules, audit-ci, Snyk integration

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Common/         # Generic components (LoadingSpinner, ErrorBoundary)
│   ├── Layout/         # Layout components (MainLayout, Sidebar, UserMenu)
│   └── ...
├── pages/              # Page components
│   ├── Dashboard/      # Dashboard page
│   ├── Servers/        # Server management pages
│   ├── Login/          # Authentication pages
│   └── ...
├── hooks/              # Custom React hooks
├── services/           # API services and external integrations
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── constants/          # Application constants
├── styles/             # Global styles and themes
└── config/             # Configuration files
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Access to the backend API

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Install security tools**:
   ```bash
   npm install -g snyk audit-ci
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development

1. **Start development server**:
   ```bash
   npm start
   ```

2. **Run with security checks**:
   ```bash
   npm run start:secure
   ```

3. **Run tests**:
   ```bash
   npm test
   ```

4. **Run E2E tests**:
   ```bash
   npm run test:e2e
   ```

### Security Operations

1. **Vulnerability scanning**:
   ```bash
   npm run security:audit
   npm run security:snyk
   ```

2. **Dependency updates**:
   ```bash
   npm run security:update
   ```

3. **Security report**:
   ```bash
   npm run security:report
   ```

### Build & Deployment

1. **Production build**:
   ```bash
   npm run build
   ```

2. **Build with security checks**:
   ```bash
   npm run build:secure
   ```

3. **Preview build**:
   ```bash
   npm run preview
   ```

## Configuration

### Environment Variables

Create a `.env` file with:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_VERSION=1.0.0
REACT_APP_ENVIRONMENT=development
```

### Security Configuration

- **CSP Headers**: Content Security Policy configured in `public/index.html`
- **ESLint Security**: Security rules enabled in `.eslintrc.json`
- **Audit Configuration**: Vulnerability thresholds in `audit-ci.json`
- **Snyk Configuration**: Security scanning in `.snyk`

## Available Scripts

| Script | Description |
|--------|-------------|
| `start` | Start development server |
| `start:secure` | Start with security checks |
| `build` | Create production build |
| `build:secure` | Build with security validation |
| `test` | Run unit tests |
| `test:coverage` | Run tests with coverage |
| `test:e2e` | Run Cypress E2E tests |
| `lint` | Run ESLint |
| `lint:fix` | Fix ESLint issues |
| `type-check` | Run TypeScript compiler |
| `security:audit` | Run npm audit |
| `security:snyk` | Run Snyk security scan |
| `security:update` | Update dependencies |
| `security:report` | Generate security report |

## Security Features

### 1. Vulnerability Scanning
- **npm audit**: Scans for known vulnerabilities
- **Snyk**: Advanced vulnerability detection
- **audit-ci**: CI/CD integration for security checks

### 2. Secure Coding Practices
- **ESLint Security Plugin**: Detects security issues
- **TypeScript Strict Mode**: Prevents common errors
- **Content Security Policy**: Prevents XSS attacks
- **Secure Headers**: HSTS, X-Frame-Options, etc.

### 3. Dependency Management
- **Package Lock**: Ensures consistent dependencies
- **Automatic Updates**: Scheduled security updates
- **Dependency Scanning**: Regular vulnerability checks

### 4. Authentication & Authorization
- **JWT Token Management**: Secure token handling
- **Role-based Access Control**: Permission-based UI
- **Session Management**: Secure session handling

## Testing Strategy

### Unit Tests
- **Framework**: Jest + React Testing Library
- **Coverage**: 80% minimum requirement
- **Location**: `src/**/*.test.ts(x)`

### Integration Tests
- **API Integration**: Mock service worker
- **Component Integration**: Full component testing
- **User Interactions**: Event simulation

### E2E Tests
- **Framework**: Cypress
- **Location**: `cypress/`
- **Coverage**: Critical user flows

## Performance Optimization

### Code Splitting
- **Route-based**: Lazy loading for pages
- **Component-based**: Dynamic imports
- **Vendor Splitting**: Separate vendor bundles

### Bundle Analysis
- **Webpack Bundle Analyzer**: Bundle size analysis
- **Performance Monitoring**: Core Web Vitals
- **Lighthouse**: Performance audits

## Deployment

### Production Build
```bash
npm run build:secure
```

### Docker Deployment
```bash
docker build -t linux-patching-frontend .
docker run -p 3000:3000 linux-patching-frontend
```

### CI/CD Integration
- **GitHub Actions**: Automated testing and deployment
- **Security Scanning**: Integrated vulnerability checks
- **Quality Gates**: Code quality and security requirements

## Monitoring & Maintenance

### Performance Monitoring
- **Real User Monitoring**: Performance metrics
- **Error Tracking**: Error monitoring and alerts
- **User Analytics**: Usage patterns and insights

### Security Monitoring
- **Vulnerability Alerts**: Automated security notifications
- **Dependency Updates**: Regular dependency maintenance
- **Security Audits**: Periodic security reviews

## Contributing

1. **Security First**: All contributions must pass security checks
2. **Code Quality**: Maintain high code quality standards
3. **Testing**: Include tests for all new features
4. **Documentation**: Update documentation for changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- **Documentation**: Check the inline documentation
- **Issues**: Create GitHub issues for bugs
- **Security**: Report security issues privately