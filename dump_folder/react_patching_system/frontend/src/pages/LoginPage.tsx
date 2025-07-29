/**
 * Login Page - React Patching System
 * Converted from Flask login template
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Paper,
  Divider,
} from '@mui/material';
import { CircularProgress } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const { login, isAuthenticated } = useAuth();
  const { showSuccess } = useNotification();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const result = await login(username, password);
      
      if (result.success) {
        showSuccess('Login successful!');
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
      } else {
        setError(result.message || 'Login failed');
      }
    } catch (error: any) {
      setError(error.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Linux Patching Portal
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Sign in to your account
          </Typography>
        </Box>

        <Card variant="outlined">
          <CardHeader 
            title="Login"
            sx={{ 
              bgcolor: 'primary.main', 
              color: 'primary.contrastText',
              '& .MuiCardHeader-title': { fontWeight: 'bold' }
            }}
          />
          <CardContent>
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {error}
                </Alert>
              )}

              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username/Email"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                helperText="Demo: patchadmin or admin | LDAP: Use your Linux username"
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                helperText="Demo: admin123 for patchadmin, admin for admin | LDAP: Use your Linux password"
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={isLoading}
                sx={{ mt: 3, mb: 2 }}
              >
                {isLoading ? <CircularProgress size={24} /> : 'Sign In'}
              </Button>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                <strong>Demo Login:</strong>
              </Typography>
              <Typography variant="body2" component="div">
                • <code>patchadmin</code> / <code>admin123</code> (Primary admin)
                <br />
                • <code>admin</code> / <code>admin</code> (Legacy admin)
              </Typography>
            </Alert>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
              Note: In production, authentication is via LDAP/nslcd with Linux credentials.
            </Typography>
          </CardContent>
        </Card>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Linux Patching Automation System © 2025
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Quarter Definition: Q1 (Nov-Jan), Q2 (Feb-Apr), Q3 (May-Jul), Q4 (Aug-Oct)
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default LoginPage;