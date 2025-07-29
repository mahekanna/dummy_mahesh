/**
 * Reports Page - React Patching System
 * Converted from Flask reports_dashboard template
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import {
  Download,
  Email,
  Refresh,
  Assessment,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import apiService, { ReportData } from '../services/api';

const ReportsPage: React.FC = () => {
  const [reportData, setReportData] = useState<ReportData['report_data'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [reportType, setReportType] = useState('daily');
  const [quarter, setQuarter] = useState('');
  const [hostGroup, setHostGroup] = useState('all');
  const [status, setStatus] = useState('all');
  const [hostGroups, setHostGroups] = useState<string[]>([]);

  const { user } = useAuth();
  const { showError, showSuccess } = useNotification();

  useEffect(() => {
    loadReportData();
  }, [reportType, quarter, hostGroup, status]);

  const loadReportData = async () => {
    try {
      setLoading(true);
      const response = await apiService.getReportsData({
        type: reportType,
        quarter: quarter || undefined,
        host_group: hostGroup,
        status: status,
      });
      
      if (response.success && response.report_data) {
        setReportData(response.report_data);
        
        // Extract host groups from breakdown
        const groups = Object.keys(response.report_data.host_group_breakdown || {});
        setHostGroups(groups);
      } else {
        showError('Failed to load report data');
      }
    } catch (err: any) {
      showError(err.message || 'Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async (type: string) => {
    try {
      const blob = await apiService.exportCSVReport({
        type,
        quarter: quarter || undefined,
        host_group: hostGroup,
        status: status,
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${type}_report_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      showSuccess('Report exported successfully');
    } catch (err: any) {
      showError(err.message || 'Failed to export report');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'scheduled':
        return 'info';
      case 'approved':
        return 'success';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  // Redirect if not admin
  if (user?.role !== 'admin') {
    return (
      <Alert severity="error">
        Access denied: Admin privileges required for reports
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
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Patching Reports Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time insights and analytics for Linux patching operations
        </Typography>
      </Box>

      {/* Report Filters */}
      <Card sx={{ mb: 3 }}>
        <CardHeader title="Report Filters" />
        <CardContent>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Report Type</InputLabel>
                <Select
                  value={reportType}
                  label="Report Type"
                  onChange={(e) => setReportType(e.target.value)}
                >
                  <MenuItem value="daily">Daily Report</MenuItem>
                  <MenuItem value="weekly">Weekly Report</MenuItem>
                  <MenuItem value="monthly">Monthly Report</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Quarter</InputLabel>
                <Select
                  value={quarter}
                  label="Quarter"
                  onChange={(e) => setQuarter(e.target.value)}
                >
                  <MenuItem value="">Current Quarter</MenuItem>
                  <MenuItem value="1">Q1 (Nov-Jan)</MenuItem>
                  <MenuItem value="2">Q2 (Feb-Apr)</MenuItem>
                  <MenuItem value="3">Q3 (May-Jul)</MenuItem>
                  <MenuItem value="4">Q4 (Aug-Oct)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Host Group</InputLabel>
                <Select
                  value={hostGroup}
                  label="Host Group"
                  onChange={(e) => setHostGroup(e.target.value)}
                >
                  <MenuItem value="all">All Groups</MenuItem>
                  {hostGroups.map((group) => (
                    <MenuItem key={group} value={group}>
                      {group.replace('_', ' ').toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={status}
                  label="Status Filter"
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="scheduled">Scheduled</MenuItem>
                  <MenuItem value="approved">Approved</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
          <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadReportData}
            >
              Refresh Data
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => handleExportCSV('summary')}
            >
              Export Summary
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              onClick={() => handleExportCSV('detailed')}
            >
              Export Detailed
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Host Group Breakdown */}
        {reportData?.host_group_breakdown && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Host Group Breakdown" />
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Host Group</TableCell>
                        <TableCell align="right">Total</TableCell>
                        <TableCell align="right">Approved</TableCell>
                        <TableCell align="right">Pending</TableCell>
                        <TableCell align="right">Completed</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(reportData.host_group_breakdown).map(([group, data]) => (
                        <TableRow key={group}>
                          <TableCell>{group.replace('_', ' ').toUpperCase()}</TableCell>
                          <TableCell align="right">{data.total}</TableCell>
                          <TableCell align="right">{data.approved}</TableCell>
                          <TableCell align="right">{data.pending}</TableCell>
                          <TableCell align="right">{data.completed}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Attention Required */}
        {reportData?.attention_required && reportData.attention_required.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Attention Required" />
              <CardContent>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Server</TableCell>
                        <TableCell>Issue</TableCell>
                        <TableCell>Owner</TableCell>
                        <TableCell>Priority</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reportData.attention_required.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{item.server}</TableCell>
                          <TableCell>{item.issue}</TableCell>
                          <TableCell>{item.owner}</TableCell>
                          <TableCell>
                            <Chip
                              label={item.priority}
                              color={getPriorityColor(item.priority)}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Completed Servers */}
        {reportData?.completed_servers && reportData.completed_servers.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Completed Patches" />
              <CardContent>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Server Name</TableCell>
                        <TableCell>Host Group</TableCell>
                        <TableCell>Patch Date</TableCell>
                        <TableCell>Patch Time</TableCell>
                        <TableCell>Completion Date</TableCell>
                        <TableCell>Duration</TableCell>
                        <TableCell>Owner</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {reportData.completed_servers.map((server, index) => (
                        <TableRow key={index}>
                          <TableCell>{server.server_name}</TableCell>
                          <TableCell>{server.host_group}</TableCell>
                          <TableCell>{server.patch_date}</TableCell>
                          <TableCell>{server.patch_time}</TableCell>
                          <TableCell>{server.completion_date}</TableCell>
                          <TableCell>{server.duration}</TableCell>
                          <TableCell>{server.owner}</TableCell>
                          <TableCell>
                            <Chip
                              label={server.status}
                              color={getStatusColor(server.status)}
                              size="small"
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* No Data Message */}
        {reportData && Object.keys(reportData).length === 0 && (
          <Grid item xs={12}>
            <Alert severity="info">
              No report data available for the selected filters.
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ReportsPage;