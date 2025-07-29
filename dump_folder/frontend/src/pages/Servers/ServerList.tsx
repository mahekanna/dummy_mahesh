/**
 * Server list page component
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Computer as ComputerIcon,
} from '@mui/icons-material';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import { PERMISSIONS, ENVIRONMENTS, OPERATING_SYSTEMS } from '@/constants';
import { formatDateTime, getOSIcon, getEnvironmentColor, debounce } from '@/utils/helpers';
import { Server, ServerFilters } from '@/types/api';

export const ServerList = () => {
  const { hasPermission } = useAuth();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState<ServerFilters>({});

  // Fetch servers
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['servers', page, rowsPerPage, searchTerm, filters],
    queryFn: () => apiService.getServers({
      page: page + 1,
      pageSize: rowsPerPage,
      search: searchTerm,
      ...filters,
    }),
    keepPreviousData: true,
  });

  const servers = data?.data.items || [];
  const totalCount = data?.data.total || 0;

  // Debounced search
  const debouncedSearch = debounce((value: string) => {
    setSearchTerm(value);
    setPage(0);
  }, 300);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    debouncedSearch(event.target.value);
  };

  const handleFilterChange = (key: keyof ServerFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(0);
  };

  const handlePageChange = (_: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleExport = async () => {
    try {
      const blob = await apiService.exportServers(filters);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `servers-${new Date().toISOString().split('T')[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  if (isLoading) {
    return <LoadingSpinner message="Loading servers..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">
          Error loading servers: {(error as Error).message}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          Servers
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          {hasPermission(PERMISSIONS.SERVERS_EXPORT) && (
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExport}
            >
              Export
            </Button>
          )}
          {hasPermission(PERMISSIONS.SERVERS_IMPORT) && (
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              component="label"
            >
              Import
              <input type="file" hidden accept=".csv" />
            </Button>
          )}
          {hasPermission(PERMISSIONS.SERVERS_CREATE) && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
            >
              Add Server
            </Button>
          )}
        </Stack>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2} alignItems="center">
            <TextField
              placeholder="Search servers..."
              variant="outlined"
              size="small"
              InputProps={{
                startAdornment: <SearchIcon sx={{ color: 'text.secondary', mr: 1 }} />,
              }}
              sx={{ minWidth: 250 }}
              onChange={handleSearchChange}
            />
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Environment</InputLabel>
              <Select
                value={filters.environments?.[0] || ''}
                onChange={(e) => handleFilterChange('environments', e.target.value ? [e.target.value] : undefined)}
              >
                <MenuItem value="">All</MenuItem>
                {ENVIRONMENTS.map(env => (
                  <MenuItem key={env.value} value={env.value}>
                    {env.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>OS</InputLabel>
              <Select
                value={filters.operatingSystems?.[0] || ''}
                onChange={(e) => handleFilterChange('operatingSystems', e.target.value ? [e.target.value] : undefined)}
              >
                <MenuItem value="">All</MenuItem>
                {OPERATING_SYSTEMS.map(os => (
                  <MenuItem key={os.value} value={os.value}>
                    {os.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.statuses?.[0] || ''}
                onChange={(e) => handleFilterChange('statuses', e.target.value ? [e.target.value] : undefined)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
                <MenuItem value="maintenance">Maintenance</MenuItem>
              </Select>
            </FormControl>
          </Stack>
        </CardContent>
      </Card>

      {/* Server Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Server Name</TableCell>
              <TableCell>Environment</TableCell>
              <TableCell>OS</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Last Patched</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {servers.map((server: Server) => (
              <TableRow key={server.id} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ComputerIcon fontSize="small" color="primary" />
                    <Box>
                      <Typography variant="subtitle2">
                        {server.serverName}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {server.hostGroup}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={server.environment}
                    size="small"
                    color={getEnvironmentColor(server.environment) as any}
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span>{getOSIcon(server.operatingSystem)}</span>
                    <Typography variant="body2">
                      {server.operatingSystem}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <StatusChip status={server.activeStatus} />
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {server.primaryOwner}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {server.lastSyncDate ? formatDateTime(server.lastSyncDate) : 'Never'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    {hasPermission(PERMISSIONS.SERVERS_UPDATE) && (
                      <Tooltip title="Edit">
                        <IconButton size="small">
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {hasPermission(PERMISSIONS.SERVERS_DELETE) && (
                      <Tooltip title="Delete">
                        <IconButton size="small" color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
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
    </Box>
  );
};