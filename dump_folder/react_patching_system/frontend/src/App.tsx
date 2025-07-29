/**
 * Main App Component - React Patching System
 * Converted from Flask web portal to React SPA
 */

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

// Components
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ServerDetailPage from './pages/ServerDetailPage';
import AdminPage from './pages/AdminPage';
import ReportsPage from './pages/ReportsPage';
import MainLayout from './components/Layout/MainLayout';
import PrivateRoute from './components/Common/PrivateRoute';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider } from './contexts/NotificationContext';

// Theme based on original Flask app colors
const theme = createTheme({
  palette: {
    primary: {
      main: '#2c3e50', // Original header color
    },
    secondary: {
      main: '#3498db', // Original secondary color
    },
    success: {
      main: '#2ecc71',
    },
    warning: {
      main: '#f1c40f',
    },
    error: {
      main: '#e74c3c',
    },
    background: {
      default: '#f5f5f5', // Original background
    },
  },
  typography: {
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <NotificationProvider>
          <Router>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* Protected routes */}
                <Route path="/" element={
                  <PrivateRoute>
                    <MainLayout />
                  </PrivateRoute>
                }>
                  <Route index element={<Navigate to="/dashboard" replace />} />
                  <Route path="dashboard" element={<DashboardPage />} />
                  <Route path="server/:serverName" element={<ServerDetailPage />} />
                  <Route path="admin" element={<AdminPage />} />
                  <Route path="reports" element={<ReportsPage />} />
                </Route>
                
                {/* Fallback route */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Box>
          </Router>
        </NotificationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;