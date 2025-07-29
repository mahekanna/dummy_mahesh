/**
 * Report generator page component
 */

import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Grid,
  Stack,
  Alert,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  GetApp as DownloadIcon,
  Email as EmailIcon,
  Description as ReportIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { toast } from 'react-hot-toast';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import { PERMISSIONS, QUARTERS, REPORT_TYPES, REPORT_FORMATS } from '@/constants';
import { formatDateTime, downloadFile } from '@/utils/helpers';
import { ReportConfig, Report } from '@/types/api';

export const ReportGenerator = () => {
  const { hasPermission } = useAuth();
  const [reportConfig, setReportConfig] = useState<Partial<ReportConfig>>({
    type: 'summary',
    format: 'pdf',
    includeDetails: true,
    includeCharts: true,
    includeAuditTrail: false,
  });
  const [emailRecipients, setEmailRecipients] = useState('');

  // Fetch existing reports
  const { data: reportsData, isLoading, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: () => apiService.getSystemStats(), // Assuming reports are in system stats
    refetchInterval: 30000,
  });

  // Generate report mutation
  const generateReportMutation = useMutation({
    mutationFn: (config: ReportConfig) => apiService.generateReport(config),
    onSuccess: (response) => {
      toast.success('Report generated successfully');
      refetch();
      // Auto-download if requested
      if (response.data.downloadUrl) {
        window.open(response.data.downloadUrl, '_blank');
      }
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to generate report');
    },
  });

  const handleConfigChange = (key: keyof ReportConfig, value: any) => {
    setReportConfig(prev => ({ ...prev, [key]: value }));
  };

  const handleGenerateReport = () => {
    if (!reportConfig.type || !reportConfig.format) {
      toast.error('Please select report type and format');
      return;
    }

    generateReportMutation.mutate(reportConfig as ReportConfig);
  };

  const handleDownloadReport = async (reportId: string) => {
    try {
      const blob = await apiService.getReport(reportId);
      downloadFile(blob, `report-${reportId}.${reportConfig.format}`);
    } catch (error) {
      toast.error('Failed to download report');
    }
  };

  const handleEmailReport = async (reportId: string) => {
    if (!emailRecipients.trim()) {
      toast.error('Please enter email recipients');
      return;
    }

    try {
      const recipients = emailRecipients.split(',').map(email => email.trim());
      await apiService.emailReport(reportId, recipients);
      toast.success('Report sent successfully');
    } catch (error) {
      toast.error('Failed to send report');
    }
  };

  // Mock reports data for demonstration
  const mockReports: Report[] = [
    {
      id: '1',
      name: 'Monthly Summary Report',
      type: 'summary',
      format: 'pdf',
      config: reportConfig as ReportConfig,
      status: 'completed',
      progress: 100,
      downloadUrl: '/api/reports/1/download',
      fileSize: 2048576,
      generatedBy: 'admin',
      generatedAt: new Date().toISOString(),
    },
    {
      id: '2',
      name: 'Q3 Patching Report',
      type: 'quarterly',
      format: 'csv',
      config: reportConfig as ReportConfig,
      status: 'generating',
      progress: 75,
      generatedBy: 'operator',
      generatedAt: new Date().toISOString(),
    },
  ];

  if (isLoading) {
    return <LoadingSpinner message="Loading reports..." />;
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Report Generator
        </Typography>

        <Grid container spacing={3}>
          {/* Report Configuration */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Generate New Report
                </Typography>

                <Stack spacing={2}>
                  <FormControl fullWidth>
                    <InputLabel>Report Type</InputLabel>
                    <Select
                      value={reportConfig.type || ''}
                      onChange={(e) => handleConfigChange('type', e.target.value)}
                    >
                      {REPORT_TYPES.map(type => (
                        <MenuItem key={type.value} value={type.value}>
                          {type.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel>Format</InputLabel>
                    <Select
                      value={reportConfig.format || ''}
                      onChange={(e) => handleConfigChange('format', e.target.value)}
                    >
                      {REPORT_FORMATS.map(format => (
                        <MenuItem key={format.value} value={format.value}>
                          {format.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {reportConfig.type === 'custom' && (
                    <>
                      <DatePicker
                        label="Start Date"
                        value={reportConfig.startDate ? new Date(reportConfig.startDate) : null}
                        onChange={(date) => handleConfigChange('startDate', date?.toISOString())}
                        renderInput={(params) => <TextField {...params} fullWidth />}
                      />

                      <DatePicker
                        label="End Date"
                        value={reportConfig.endDate ? new Date(reportConfig.endDate) : null}
                        onChange={(date) => handleConfigChange('endDate', date?.toISOString())}
                        renderInput={(params) => <TextField {...params} fullWidth />}
                      />
                    </>
                  )}

                  {reportConfig.type === 'quarterly' && (
                    <FormControl fullWidth>
                      <InputLabel>Quarter</InputLabel>
                      <Select
                        value={reportConfig.quarter || ''}
                        onChange={(e) => handleConfigChange('quarter', e.target.value)}
                      >
                        {QUARTERS.map(quarter => (
                          <MenuItem key={quarter.value} value={quarter.value}>
                            {quarter.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}

                  <Typography variant="subtitle2" gutterBottom>
                    Report Options
                  </Typography>

                  <Stack spacing={1}>
                    <label>
                      <input
                        type="checkbox"
                        checked={reportConfig.includeDetails || false}
                        onChange={(e) => handleConfigChange('includeDetails', e.target.checked)}
                      />
                      {' '}Include detailed information
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={reportConfig.includeCharts || false}
                        onChange={(e) => handleConfigChange('includeCharts', e.target.checked)}
                      />
                      {' '}Include charts and graphs
                    </label>
                    <label>
                      <input
                        type="checkbox"
                        checked={reportConfig.includeAuditTrail || false}
                        onChange={(e) => handleConfigChange('includeAuditTrail', e.target.checked)}
                      />
                      {' '}Include audit trail
                    </label>
                  </Stack>

                  <TextField
                    label="Email Recipients (comma-separated)"
                    value={emailRecipients}
                    onChange={(e) => setEmailRecipients(e.target.value)}
                    placeholder="user1@example.com, user2@example.com"
                    fullWidth
                    multiline
                    rows={2}
                  />

                  <Button
                    variant="contained"
                    startIcon={<ReportIcon />}
                    onClick={handleGenerateReport}
                    disabled={generateReportMutation.isPending || !hasPermission(PERMISSIONS.REPORTS_GENERATE)}
                    fullWidth
                  >
                    {generateReportMutation.isPending ? 'Generating...' : 'Generate Report'}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          {/* Generated Reports */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">
                    Generated Reports
                  </Typography>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={() => refetch()}
                  >
                    Refresh
                  </Button>
                </Box>

                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Report Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Generated By</TableCell>
                        <TableCell>Generated At</TableCell>
                        <TableCell>Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {mockReports.map((report) => (
                        <TableRow key={report.id}>
                          <TableCell>
                            <Box>
                              <Typography variant="subtitle2">
                                {report.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {report.format.toUpperCase()}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip label={report.type} size="small" variant="outlined" />
                          </TableCell>
                          <TableCell>
                            <Box>
                              <StatusChip status={report.status} />
                              {report.status === 'generating' && (
                                <LinearProgress
                                  variant="determinate"
                                  value={report.progress}
                                  sx={{ mt: 1, width: 100 }}
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {report.generatedBy}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDateTime(report.generatedAt)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Stack direction="row" spacing={1}>
                              {report.status === 'completed' && (
                                <>
                                  <Tooltip title="Download">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleDownloadReport(report.id)}
                                      disabled={!hasPermission(PERMISSIONS.REPORTS_DOWNLOAD)}
                                    >
                                      <DownloadIcon />
                                    </IconButton>
                                  </Tooltip>
                                  <Tooltip title="Email">
                                    <IconButton
                                      size="small"
                                      onClick={() => handleEmailReport(report.id)}
                                      disabled={!hasPermission(PERMISSIONS.REPORTS_EMAIL)}
                                    >
                                      <EmailIcon />
                                    </IconButton>
                                  </Tooltip>
                                </>
                              )}
                            </Stack>
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
    </LocalizationProvider>
  );
};