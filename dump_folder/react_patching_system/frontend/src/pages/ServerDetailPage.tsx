/**
 * Server Detail Page - React Patching System
 * Converted from Flask server_detail template
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Table,
  TableBody,
  TableCell,
  TableRow,
  Chip,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import apiService, { Server } from '../services/api';

const ServerDetailPage: React.FC = () => {
  const { serverName } = useParams<{ serverName: string }>();
  const [server, setServer] = useState<Server | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentQuarter, setCurrentQuarter] = useState('');

  const { user } = useAuth();
  const { showError } = useNotification();
  const navigate = useNavigate();

  useEffect(() => {
    if (serverName) {
      loadServer();
    }
  }, [serverName]);

  const loadServer = async () => {
    if (!serverName) return;
    
    try {
      setLoading(true);
      const response = await apiService.getServer(serverName);
      
      if (response.success && response.data) {
        setServer(response.data);
        setCurrentQuarter(response.currentQuarter || '');
      } else {
        setError(response.message || 'Failed to load server');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load server');
      showError(err.message || 'Failed to load server');
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

  const getCurrentQuarterApprovalStatus = (server: Server) => {
    const currentQ = currentQuarter;
    const approvalField = `q${currentQ}ApprovalStatus` as keyof Server;
    return server[approvalField] as string || 'Pending';
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
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  if (!server) {
    return (
      <Box>
        <Alert severity="error" sx={{ mb: 2 }}>
          Server not found
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBack />}
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </Button>
        <Typography variant="h4" component="h1">
          Server: {server.serverName}
        </Typography>
        <Chip
          label={server.currentQuarterStatus}
          color={getStatusColor(server.currentQuarterStatus)}
          size="medium"
        />
      </Box>

      <Grid container spacing={3}>
        {/* Server Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Server Information" />
            <CardContent>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell variant="head">Server Name:</TableCell>
                    <TableCell>{server.serverName}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Timezone:</TableCell>
                    <TableCell>{server.serverTimezone}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Primary Owner:</TableCell>
                    <TableCell>{server.primaryOwner}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Secondary Owner:</TableCell>
                    <TableCell>{server.secondaryOwner || 'Not set'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Host Group:</TableCell>
                    <TableCell>{server.hostGroup}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Location:</TableCell>
                    <TableCell>{server.location || 'Not set'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Incident Ticket:</TableCell>
                    <TableCell>{server.incidentTicket || 'Not set'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Patcher Email:</TableCell>
                    <TableCell>{server.patcherEmail || 'Not set'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Q{currentQuarter} Approval:</TableCell>
                    <TableCell>
                      <Chip
                        label={getCurrentQuarterApprovalStatus(server)}
                        color={getStatusColor(getCurrentQuarterApprovalStatus(server))}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell variant="head">Status:</TableCell>
                    <TableCell>{server.currentQuarterStatus}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </Grid>

        {/* Current Schedule */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Current Schedule" />
            <CardContent>
              <Grid container spacing={2}>
                {[
                  { quarter: '1', label: 'Q1' },
                  { quarter: '2', label: 'Q2' },
                  { quarter: '3', label: 'Q3' },
                  { quarter: '4', label: 'Q4' },
                ].map(({ quarter, label }) => (
                  <Grid item xs={12} sm={6} key={quarter}>
                    <Card variant="outlined" sx={{ bgcolor: quarter === currentQuarter ? 'action.selected' : 'inherit' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {label}
                          {quarter === currentQuarter && (
                            <Chip label="Current" color="info" size="small" sx={{ ml: 1 }} />
                          )}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Date:</strong> {server[`q${quarter}PatchDate` as keyof Server] as string || 'Not scheduled'}
                        </Typography>
                        <Typography variant="body2">
                          <strong>Time:</strong> {server[`q${quarter}PatchTime` as keyof Server] as string || 'Not scheduled'}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Important Notes */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Important Notes" />
            <CardContent>
              <Box component="ul" sx={{ m: 0, pl: 2 }}>
                <li>All times are in <strong>{server.serverTimezone}</strong> timezone</li>
                <li>Default patching windows are Thursday evenings</li>
                <li>Schedule changes are locked from Thursday to Tuesday</li>
                <li>Pre-checks will be performed 5 hours before patching</li>
                <li>You will receive email notifications throughout the process</li>
                {user?.role === 'admin' && (
                  <li><strong>Admin privileges:</strong> You can modify all server settings and view all servers</li>
                )}
                {user?.role === 'user' && (
                  <li><strong>User privileges:</strong> You can only modify schedules for servers you own</li>
                )}
                {user?.role === 'readonly' && (
                  <li><strong>Read-only access:</strong> You can view server information but cannot make changes</li>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ServerDetailPage;