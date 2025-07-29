/**
 * Dashboard Page - React Patching System
 * Converted from Flask dashboard template
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
} from '@mui/material';
import {
  Settings,
  CheckCircle,
  Schedule,
  Warning,
  Error,
  Info,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import apiService, { Server } from '../services/api';

const DashboardPage: React.FC = () => {
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentQuarter, setCurrentQuarter] = useState('');
  const [quarterName, setQuarterName] = useState('');
  const [error, setError] = useState('');

  const { user } = useAuth();
  const { showError, showSuccess } = useNotification();
  const navigate = useNavigate();

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const response = await apiService.getServers();
      
      if (response.success && response.data) {
        setServers(response.data);
        setCurrentQuarter(response.currentQuarter || '');
        
        // Get quarter name
        const quartersResponse = await apiService.getQuartersInfo();
        if (quartersResponse.success && quartersResponse.data) {
          const quarterInfo = quartersResponse.data.quarters[response.currentQuarter || ''];
          setQuarterName(quarterInfo?.name || `Q${response.currentQuarter}`);
        }
      } else {
        setError(response.message || 'Failed to load servers');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load servers');
      showError(err.message || 'Failed to load servers');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'success';
      case 'pending':
        return 'warning';
      case 'scheduled':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return <CheckCircle fontSize="small" />;
      case 'pending':
        return <Warning fontSize="small" />;
      case 'scheduled':
        return <Schedule fontSize="small" />;
      case 'completed':
        return <CheckCircle fontSize="small" />;
      case 'failed':
        return <Error fontSize="small" />;
      default:
        return <Info fontSize="small" />;
    }
  };

  const getQuarterDescription = (quarter: string) => {
    const descriptions: { [key: string]: string } = {
      '1': 'November to January',
      '2': 'February to April',
      '3': 'May to July',
      '4': 'August to October',
    };
    return descriptions[quarter] || 'Unknown';
  };

  const getCurrentQuarterSchedule = (server: Server) => {
    const currentQ = currentQuarter;
    const dateField = `q${currentQ}PatchDate` as keyof Server;
    const timeField = `q${currentQ}PatchTime` as keyof Server;
    
    const date = server[dateField] as string;
    const time = server[timeField] as string;
    
    if (date && time) {
      return `${date} ${time}`;
    }
    return 'Not scheduled';
  };

  const getCurrentQuarterApprovalStatus = (server: Server) => {
    const currentQ = currentQuarter;
    const approvalField = `q${currentQ}ApprovalStatus` as keyof Server;
    return server[approvalField] as string || 'Pending';
  };

  const handleServerClick = (serverName: string) => {
    navigate(`/server/${encodeURIComponent(serverName)}`);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Grid container spacing={3}>
        {/* Header Info */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Current Quarter: {quarterName}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Months covered: {getQuarterDescription(currentQuarter)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* User Info */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title={`Welcome, ${user?.name}`} />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" fontWeight="bold">
                    Role:
                  </Typography>
                  <Chip
                    label={user?.role === 'admin' ? 'Administrator' : user?.role === 'user' ? 'User' : 'Read Only'}
                    color={user?.role === 'admin' ? 'error' : user?.role === 'user' ? 'primary' : 'default'}
                    size="small"
                  />
                </Box>
                {user?.role === 'admin' && (
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<Settings />}
                    onClick={() => navigate('/admin')}
                  >
                    Admin Panel
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Servers Table */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="h6">
                    {user?.role === 'admin' ? 'All Servers' : 'Your Servers'}
                  </Typography>
                  {user?.role === 'admin' && (
                    <Chip label="Admin View" color="warning" size="small" />
                  )}
                </Box>
              }
            />
            <CardContent>
              {servers.length === 0 ? (
                <Alert severity="info">
                  No servers found for your account.
                </Alert>
              ) : (
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Server Name</TableCell>
                        <TableCell>Timezone</TableCell>
                        <TableCell>{quarterName} Schedule</TableCell>
                        <TableCell>Approval Status</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Primary Owner</TableCell>
                        <TableCell>Secondary Owner</TableCell>
                        <TableCell>Location</TableCell>
                        <TableCell>Incident</TableCell>
                        <TableCell>Patcher Email</TableCell>
                        <TableCell>AI Recommendation</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {servers.map((server) => (
                        <TableRow key={server.id} hover>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {server.serverName}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {server.serverTimezone}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {getCurrentQuarterSchedule(server)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={getCurrentQuarterApprovalStatus(server)}
                              color={getStatusColor(getCurrentQuarterApprovalStatus(server))}
                              size="small"
                              icon={getStatusIcon(getCurrentQuarterApprovalStatus(server))}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={server.currentQuarterStatus}
                              color={getStatusColor(server.currentQuarterStatus)}
                              size="small"
                              icon={getStatusIcon(server.currentQuarterStatus)}
                            />
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={server.primaryOwner || 'Not set'}
                              color="primary"
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            {server.secondaryOwner ? (
                              <Chip
                                label={server.secondaryOwner}
                                color="default"
                                size="small"
                                variant="outlined"
                              />
                            ) : (
                              <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                Not set
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {server.location || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {server.incidentTicket || 'Not set'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {server.patcherEmail || 'Not set'}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={getCurrentQuarterSchedule(server) === 'Not scheduled' ? 'Available' : 'Scheduled'}
                              color={getCurrentQuarterSchedule(server) === 'Not scheduled' ? 'info' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="contained"
                              size="small"
                              onClick={() => handleServerClick(server.serverName)}
                            >
                              Manage
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Instructions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Instructions" />
            <CardContent>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                <li>Click "Manage" to schedule or modify patching times for each server</li>
                <li>Default patching day is Thursday, but you can choose any available date</li>
                <li>Changes are locked during freeze period (Thursday to Tuesday)</li>
                <li>You'll receive email notifications before and after patching</li>
                <li>All times should be specified in the server's local timezone</li>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Upcoming Quarters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Upcoming Quarters" />
            <CardContent>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Quarter</TableCell>
                      <TableCell>Months</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {['1', '2', '3', '4'].map((quarter) => (
                      <TableRow 
                        key={quarter}
                        sx={{ 
                          bgcolor: quarter === currentQuarter ? 'action.selected' : 'inherit' 
                        }}
                      >
                        <TableCell>
                          <Typography variant="body2" fontWeight={quarter === currentQuarter ? 'bold' : 'normal'}>
                            Q{quarter}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {getQuarterDescription(quarter)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;