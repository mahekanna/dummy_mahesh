/**
 * Main Layout Component - React Patching System
 * Converted from Flask base template
 */

import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Avatar,
  Divider,
} from '@mui/material';
import {
  AccountCircle,
  Dashboard,
  Assessment,
  AdminPanelSettings,
  ExitToApp,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNotification } from '../../contexts/NotificationContext';

const MainLayout: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const { user, logout } = useAuth();
  const { showSuccess } = useNotification();
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleClose();
    await logout();
    showSuccess('Logged out successfully');
    navigate('/login');
  };

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'user':
        return 'primary';
      case 'readonly':
        return 'default';
      default:
        return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator';
      case 'user':
        return 'User';
      case 'readonly':
        return 'Read Only';
      default:
        return role;
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Linux Patching Portal
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button
              color="inherit"
              startIcon={<Dashboard />}
              onClick={() => handleNavigation('/dashboard')}
              sx={{ 
                bgcolor: isActive('/dashboard') ? 'rgba(255,255,255,0.1)' : 'transparent',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
              }}
            >
              Dashboard
            </Button>

            <Button
              color="inherit"
              startIcon={<Assessment />}
              onClick={() => handleNavigation('/reports')}
              sx={{ 
                bgcolor: isActive('/reports') ? 'rgba(255,255,255,0.1)' : 'transparent',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
              }}
            >
              Reports
            </Button>

            {user?.role === 'admin' && (
              <Button
                color="inherit"
                startIcon={<AdminPanelSettings />}
                onClick={() => handleNavigation('/admin')}
                sx={{ 
                  bgcolor: isActive('/admin') ? 'rgba(255,255,255,0.1)' : 'transparent',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' }
                }}
              >
                Admin Panel
              </Button>
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 2 }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                <Typography variant="body2" sx={{ color: 'inherit', lineHeight: 1.2 }}>
                  Welcome, {user?.name}
                </Typography>
                <Chip
                  label={getRoleLabel(user?.role || 'user')}
                  size="small"
                  color={getRoleColor(user?.role || 'user')}
                  sx={{ mt: 0.5, height: 20, fontSize: '0.75rem' }}
                />
              </Box>

              <IconButton
                size="large"
                aria-label="account of current user"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircle />
              </IconButton>

              <Menu
                id="menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorEl)}
                onClose={handleClose}
              >
                <MenuItem disabled>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Typography variant="body2" fontWeight="bold">
                      {user?.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user?.email}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user?.auth_method === 'ldap' ? 'LDAP Authentication' : 'Local Authentication'}
                    </Typography>
                  </Box>
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                  <ExitToApp sx={{ mr: 1 }} />
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ flexGrow: 1, py: 3 }}>
        <Outlet />
      </Container>

      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          mt: 'auto',
          borderTop: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
          textAlign: 'center',
        }}
      >
        <Typography variant="body2" color="text.secondary">
          Linux Patching Automation System © 2025 | Quarter Definition: Q1 (Nov-Jan), Q2 (Feb-Apr), Q3 (May-Jul), Q4 (Aug-Oct)
        </Typography>
      </Box>
    </Box>
  );
};

export default MainLayout;