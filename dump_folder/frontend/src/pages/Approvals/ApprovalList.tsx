/**
 * Approval list page component
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
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
  Checkbox,
  Alert,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Check as CheckIcon,
  Close as CloseIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  CheckCircle as ApproveIcon,
  Cancel as RejectIcon,
} from '@mui/icons-material';
import { toast } from 'react-hot-toast';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import { PERMISSIONS, QUARTERS } from '@/constants';
import { formatDateTime, formatRelativeTime } from '@/utils/helpers';
import { ApprovalRequest } from '@/types/api';

export const ApprovalList = () => {
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedApprovals, setSelectedApprovals] = useState<string[]>([]);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'approve' | 'reject'>('approve');
  const [actionComment, setActionComment] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    quarter: '',
  });

  // Fetch approval requests
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['approval-requests', page, rowsPerPage, filters],
    queryFn: () => apiService.getApprovalRequests({
      page: page + 1,
      pageSize: rowsPerPage,
      ...filters,
    }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Approve servers mutation
  const approveServersMutation = useMutation({
    mutationFn: (data: { approvalIds: string[]; comment?: string }) => 
      apiService.approveServers(data.approvalIds, data.comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-requests'] });
      setActionDialogOpen(false);
      setSelectedApprovals([]);
      setActionComment('');
      toast.success('Servers approved successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to approve servers');
    },
  });

  // Reject servers mutation
  const rejectServersMutation = useMutation({
    mutationFn: (data: { approvalIds: string[]; reason: string }) => 
      apiService.rejectServers(data.approvalIds, data.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approval-requests'] });
      setActionDialogOpen(false);
      setSelectedApprovals([]);
      setActionComment('');
      toast.success('Servers rejected successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to reject servers');
    },
  });

  const approvals = data?.data.items || [];
  const totalCount = data?.data.total || 0;

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      const pendingApprovals = approvals
        .filter(approval => approval.status === 'pending')
        .map(approval => approval.id);
      setSelectedApprovals(pendingApprovals);
    } else {
      setSelectedApprovals([]);
    }
  };

  const handleSelectApproval = (approvalId: string) => {
    setSelectedApprovals(prev => 
      prev.includes(approvalId)
        ? prev.filter(id => id !== approvalId)
        : [...prev, approvalId]
    );
  };

  const handleAction = (type: 'approve' | 'reject') => {
    if (selectedApprovals.length === 0) {
      toast.error('Please select at least one approval request');
      return;
    }
    setActionType(type);
    setActionDialogOpen(true);
  };

  const confirmAction = () => {
    if (actionType === 'approve') {
      approveServersMutation.mutate({
        approvalIds: selectedApprovals,
        comment: actionComment,
      });
    } else {
      if (!actionComment.trim()) {
        toast.error('Please provide a reason for rejection');
        return;
      }
      rejectServersMutation.mutate({
        approvalIds: selectedApprovals,
        reason: actionComment,
      });
    }
  };

  const pendingApprovals = approvals.filter(approval => approval.status === 'pending');
  const isAllSelected = pendingApprovals.length > 0 && 
    pendingApprovals.every(approval => selectedApprovals.includes(approval.id));

  if (isLoading) {
    return <LoadingSpinner message="Loading approval requests..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading approval requests: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Approval Requests
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          {hasPermission(PERMISSIONS.APPROVALS_APPROVE) && selectedApprovals.length > 0 && (
            <>
              <Button
                variant="contained"
                color="success"
                startIcon={<ApproveIcon />}
                onClick={() => handleAction('approve')}
              >
                Approve ({selectedApprovals.length})
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<RejectIcon />}
                onClick={() => handleAction('reject')}
              >
                Reject ({selectedApprovals.length})
              </Button>
            </>
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
                <MenuItem value="approved">Approved</MenuItem>
                <MenuItem value="rejected">Rejected</MenuItem>
                <MenuItem value="expired">Expired</MenuItem>
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

      {/* Approvals Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={isAllSelected}
                  indeterminate={
                    selectedApprovals.length > 0 && selectedApprovals.length < pendingApprovals.length
                  }
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Server</TableCell>
              <TableCell>Quarter</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Requested By</TableCell>
              <TableCell>Request Date</TableCell>
              <TableCell>Approver</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {approvals.map((approval: ApprovalRequest) => (
              <TableRow key={approval.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedApprovals.includes(approval.id)}
                    onChange={() => handleSelectApproval(approval.id)}
                    disabled={approval.status !== 'pending'}
                  />
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="subtitle2">
                      {approval.serverName}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {approval.approvalType}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip label={approval.quarter} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <StatusChip status={approval.status} />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {approval.requestedBy}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDateTime(approval.requestDate)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatRelativeTime(approval.requestDate)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {approval.approver || '-'}
                  </Typography>
                  {approval.approvalDate && (
                    <Typography variant="caption" color="text.secondary">
                      {formatRelativeTime(approval.approvalDate)}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    <Tooltip title="View Details">
                      <IconButton size="small">
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    {approval.status === 'pending' && hasPermission(PERMISSIONS.APPROVALS_APPROVE) && (
                      <>
                        <Tooltip title="Approve">
                          <IconButton 
                            size="small" 
                            color="success"
                            onClick={() => {
                              setSelectedApprovals([approval.id]);
                              handleAction('approve');
                            }}
                          >
                            <CheckIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Reject">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => {
                              setSelectedApprovals([approval.id]);
                              handleAction('reject');
                            }}
                          >
                            <CloseIcon />
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

      {/* Action Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)}>
        <DialogTitle>
          {actionType === 'approve' ? 'Approve' : 'Reject'} Servers
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            {actionType === 'approve' 
              ? `Are you sure you want to approve ${selectedApprovals.length} server(s) for patching?`
              : `Are you sure you want to reject ${selectedApprovals.length} server(s) for patching?`
            }
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label={actionType === 'approve' ? 'Comment (optional)' : 'Reason for rejection (required)'}
            value={actionComment}
            onChange={(e) => setActionComment(e.target.value)}
            sx={{ mt: 2 }}
            required={actionType === 'reject'}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={confirmAction}
            variant="contained"
            color={actionType === 'approve' ? 'success' : 'error'}
            disabled={
              approveServersMutation.isPending || 
              rejectServersMutation.isPending ||
              (actionType === 'reject' && !actionComment.trim())
            }
          >
            {approveServersMutation.isPending || rejectServersMutation.isPending
              ? `${actionType === 'approve' ? 'Approving' : 'Rejecting'}...`
              : actionType === 'approve' ? 'Approve' : 'Reject'
            }
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};