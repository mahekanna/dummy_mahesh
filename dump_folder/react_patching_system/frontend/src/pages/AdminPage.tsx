/**
 * Admin Page - React Patching System
 * Converted from Flask admin_advanced template
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Divider,
} from '@mui/material';
import {
  Settings,
  Assessment,
  Sync,
  CleaningServices,
  Backup,
  Psychology,
  Timeline,
  Email,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import apiService, { SystemStats } from '../services/api';

const AdminPage: React.FC = () => {
  const [stats, setStats] = useState<SystemStats['stats'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [operationLoading, setOperationLoading] = useState<string | null>(null);

  const { user } = useAuth();
  const { showError, showSuccess, showInfo } = useNotification();

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const response = await apiService.getSystemStats();
      
      if (response.success && response.stats) {
        setStats(response.stats);
      } else {
        showError('Failed to load system statistics');
      }
    } catch (err: any) {
      showError(err.message || 'Failed to load system statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleOperation = async (operation: string, apiCall: () => Promise<any>) => {
    try {
      setOperationLoading(operation);
      const response = await apiCall();
      
      if (response.success) {
        showSuccess(response.message || `${operation} completed successfully`);
        // Reload stats after certain operations
        if (['sync', 'cleanup', 'backup'].includes(operation)) {
          loadStats();
        }
      } else {
        showError(response.message || `${operation} failed`);
      }
    } catch (err: any) {
      showError(err.message || `${operation} failed`);
    } finally {
      setOperationLoading(null);
    }
  };

  const handleGenerateReport = (reportType: string) => {
    handleOperation(
      `Generate ${reportType} report`,
      () => apiService.generateAdminReport(reportType)
    );
  };

  const handleSyncDatabase = () => {
    handleOperation('Database sync', () => apiService.syncDatabase());
  };

  const handleIntelligentScheduling = () => {
    handleOperation('Intelligent scheduling', () => apiService.runIntelligentScheduling());
  };

  const handleTestEmail = () => {
    const recipient = user?.email || 'admin@example.com';
    handleOperation(
      'Test email',
      () => apiService.testEmail(recipient)
    );
  };

  // Redirect if not admin
  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        Access denied: Admin privileges required
      </Alert>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          🛠️ Advanced Admin Panel
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Comprehensive system administration and configuration management
        </Typography>
        <Chip label="Administrator Access" color="error" sx={{ mt: 1 }} />
      </Box>

      <Grid container spacing={3}>
        {/* System Status Overview */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="📊 System Status Overview" />
            <CardContent>
              {stats && (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div">
                        {stats.overview.total_servers}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Servers
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div" color="success.main">
                        {stats.overview.approved}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Approved
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div" color="warning.main">
                        {stats.overview.pending}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Pending
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div" color="info.main">
                        {stats.overview.scheduled}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Scheduled
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div" color="success.main">
                        {stats.overview.completed}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Completed
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} sm={6} md={2}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" component="div" color="error.main">
                        {stats.overview.failed}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Failed
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Reports & Analytics */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="📊 Reports & Analytics" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Email Reports
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Assessment />}
                  onClick={() => handleGenerateReport('daily')}
                  disabled={operationLoading === 'Generate daily report'}
                  fullWidth
                >
                  📅 Send Daily Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Assessment />}
                  onClick={() => handleGenerateReport('weekly')}
                  disabled={operationLoading === 'Generate weekly report'}
                  fullWidth
                >
                  📊 Send Weekly Report
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Assessment />}
                  onClick={() => handleGenerateReport('monthly')}
                  disabled={operationLoading === 'Generate monthly report'}
                  fullWidth
                >
                  📋 Send Monthly Report
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Maintenance */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="🔄 System Maintenance" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Database Operations
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Sync />}
                  onClick={handleSyncDatabase}
                  disabled={operationLoading === 'Database sync'}
                  fullWidth
                >
                  🔄 Sync CSV to Database
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<CleaningServices />}
                  onClick={() => handleOperation('Data cleanup', () => Promise.resolve({ success: true, message: 'Cleanup would be performed' }))}
                  disabled={operationLoading === 'Data cleanup'}
                  fullWidth
                >
                  🧹 Cleanup Old Data
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Backup />}
                  onClick={() => handleOperation('Backup data', () => Promise.resolve({ success: true, message: 'Backup would be created' }))}
                  disabled={operationLoading === 'Backup data'}
                  fullWidth
                >
                  💾 Backup Data
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* AI & Automation */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="🤖 AI & Automation" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Typography variant="h6" gutterBottom>
                  Intelligent Operations
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<Psychology />}
                  onClick={handleIntelligentScheduling}
                  disabled={operationLoading === 'Intelligent scheduling'}
                  fullWidth
                >
                  🧠 Run Intelligent Scheduling
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Timeline />}
                  onClick={() => handleOperation('Analyze patterns', () => Promise.resolve({ success: true, message: 'Pattern analysis would be performed' }))}
                  disabled={operationLoading === 'Analyze patterns'}
                  fullWidth
                >
                  📈 Analyze Load Patterns
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Psychology />}
                  onClick={() => handleOperation('Generate predictions', () => Promise.resolve({ success: true, message: 'Predictions would be generated' }))}
                  disabled={operationLoading === 'Generate predictions'}
                  fullWidth
                >
                  🔮 Generate Predictions
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Testing */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="🧪 System Testing" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Test System Components
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button
                    variant="outlined"
                    startIcon={<Email />}
                    onClick={handleTestEmail}
                    disabled={operationLoading === 'Test email'}
                  >
                    📧 Test Email Configuration
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Settings />}
                    disabled
                  >
                    🔍 Test LDAP Connection
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Settings />}
                    disabled
                  >
                    💾 Test Database Connection
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Host Group Information */}
        {stats && Object.keys(stats.host_groups).length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardHeader title="🏗️ Host Group Information" />
              <CardContent>
                <Grid container spacing={2}>
                  {Object.entries(stats.host_groups).map(([group, count]) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={group}>
                      <Card variant="outlined">
                        <CardContent>
                          <Typography variant="h6" gutterBottom>
                            {group.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <Typography variant="h4" color="primary">
                            {count}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            servers
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default AdminPage;