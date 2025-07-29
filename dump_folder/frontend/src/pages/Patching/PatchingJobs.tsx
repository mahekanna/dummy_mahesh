/**
 * Patching jobs page component
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Stack,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import { PERMISSIONS, QUARTERS } from '@/constants';
import { formatDateTime, formatDuration } from '@/utils/helpers';
import { PatchingJob } from '@/types/api';

export const PatchingJobs = () => {
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedJob, setSelectedJob] = useState<PatchingJob | null>(null);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    quarter: '',
  });

  // Fetch patching jobs
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['patching-jobs', page, rowsPerPage, filters],
    queryFn: () => apiService.getPatchingJobs({
      page: page + 1,
      pageSize: rowsPerPage,
      ...filters,
    }),
    refetchInterval: 5000, // Refresh every 5 seconds for live updates
  });

  // Cancel job mutation
  const cancelJobMutation = useMutation({
    mutationFn: (jobId: string) => apiService.cancelPatchingJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patching-jobs'] });
      setCancelDialogOpen(false);
      setSelectedJob(null);
      toast.success('Job cancelled successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to cancel job');
    },
  });

  const jobs = data?.data.items || [];
  const totalCount = data?.data.total || 0;

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleCancelJob = (job: PatchingJob) => {
    setSelectedJob(job);
    setCancelDialogOpen(true);
  };

  const confirmCancelJob = () => {
    if (selectedJob) {
      cancelJobMutation.mutate(selectedJob.id);
    }
  };

  const getProgressColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'running':
        return 'primary';
      default:
        return 'primary';
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading patching jobs..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading patching jobs: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Patching Jobs
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          {hasPermission(PERMISSIONS.PATCHING_START) && (
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
            >
              Start Patching
            </Button>
          )}
        </Stack>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Quarter</InputLabel>
              <Select
                value={filters.quarter}
                onChange={(e) => setFilters(prev => ({ ...prev, quarter: e.target.value }))}
              >
                <MenuItem value="">All</MenuItem>
                {QUARTERS.map(quarter => (
                  <MenuItem key={quarter.value} value={quarter.value}>
                    {quarter.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      {/* Jobs Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Job Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Servers</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Operator</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {jobs.map((job: PatchingJob) => (
              <TableRow key={job.id} hover>
                <TableCell>
                  <Box>
                    <Typography variant="subtitle2">
                      {job.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {job.type} • {job.quarter}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <StatusChip status={job.status} />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={job.progress}
                      color={getProgressColor(job.status) as any}
                      sx={{ width: 80, height: 6 }}
                    />
                    <Typography variant="body2">
                      {job.progress}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">
                      {job.successCount + job.failureCount} / {job.totalCount}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {job.successCount} success, {job.failureCount} failed
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {job.startedAt ? formatDateTime(job.startedAt) : 'Not started'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {job.duration ? formatDuration(job.duration) : '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {job.operator}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    {job.status === 'running' && hasPermission(PERMISSIONS.PATCHING_CANCEL) && (
                      <Tooltip title="Cancel Job">
                        <IconButton size="small" color="error" onClick={() => handleCancelJob(job)}>
                          <StopIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Download Logs">
                      <IconButton size="small">
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      <TablePagination
        rowsPerPageOptions={[10, 25, 50, 100]}
        component="div"
        count={totalCount}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handlePageChange}
        onRowsPerPageChange={handleRowsPerPageChange}
      />

      {/* Cancel Job Dialog */}
      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)}>
        <DialogTitle>Cancel Patching Job</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to cancel the patching job "{selectedJob?.name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone. Any servers currently being patched will be stopped.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmCancelJob} 
            color="error" 
            variant="contained"
            disabled={cancelJobMutation.isPending}
          >
            {cancelJobMutation.isPending ? 'Cancelling...' : 'Cancel Job'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};