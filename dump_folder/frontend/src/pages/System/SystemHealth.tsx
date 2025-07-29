/**
 * System health page component
 */

import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Alert,
  LinearProgress,
  Chip,
  Stack,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { formatRelativeTime, formatBytes } from '@/utils/helpers';
import { SystemHealth as SystemHealthType, HealthStatus } from '@/types/api';

interface HealthCardProps {
  title: string;
  status: HealthStatus;
  icon: React.ReactNode;
}

const HealthCard = ({ title, status, icon }: HealthCardProps) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'critical':
        return <ErrorIcon color="error" />;
      default:
        return <ErrorIcon color="disabled" />;
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ color: 'primary.main' }}>
            {icon}
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" gutterBottom>
              {title}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {getStatusIcon(status.status)}
              <StatusChip status={status.status} />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {status.message}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Last checked: {formatRelativeTime(status.lastCheck)}
            </Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export const SystemHealth = () => {
  // Fetch system health
  const { data: healthData, isLoading, error, refetch } = useQuery({
    queryKey: ['system-health'],
    queryFn: () => apiService.getSystemHealth(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch system stats
  const { data: statsData } = useQuery({
    queryKey: ['system-stats'],
    queryFn: () => apiService.getSystemStats(),
    refetchInterval: 30000,
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading system health..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading system health: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  const health: SystemHealthType = healthData?.data || {
    overall: 'critical',
    components: {
      database: { status: 'healthy', message: 'All connections healthy', lastCheck: new Date().toISOString() },
      ssh: { status: 'healthy', message: 'SSH connectivity normal', lastCheck: new Date().toISOString() },
      email: { status: 'warning', message: 'Email queue backed up', lastCheck: new Date().toISOString() },
      logging: { status: 'healthy', message: 'Logging service operational', lastCheck: new Date().toISOString() },
      storage: { status: 'healthy', message: 'Storage utilization normal', lastCheck: new Date().toISOString() },
      memory: { status: 'warning', message: 'Memory usage at 78%', lastCheck: new Date().toISOString() },
      cpu: { status: 'healthy', message: 'CPU utilization normal', lastCheck: new Date().toISOString() },
    },
    metrics: {
      uptime: 86400 * 7, // 7 days
      totalServers: 150,
      activeConnections: 25,
      queueSize: 12,
      averageResponseTime: 150,
      errorRate: 0.02,
    },
    timestamp: new Date().toISOString(),
  };

  const stats = statsData?.data || {};

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">
          System Health
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => refetch()}
        >
          Refresh
        </Button>
      </Box>

      {/* Overall Health Status */}
      <Alert
        severity={health.overall === 'healthy' ? 'success' : health.overall === 'warning' ? 'warning' : 'error'}
        sx={{ mb: 3 }}
      >
        <Typography variant="h6">
          System Status: {health.overall.toUpperCase()}
        </Typography>
        <Typography variant="body2">
          Last updated: {formatRelativeTime(health.timestamp)}
        </Typography>
      </Alert>

      {/* Component Health Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <HealthCard
            title="Database"
            status={health.components.database}
            icon={<StorageIcon sx={{ fontSize: 32 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <HealthCard
            title="SSH Service"
            status={health.components.ssh}
            icon={<ComputerIcon sx={{ fontSize: 32 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <HealthCard
            title="Memory"
            status={health.components.memory}
            icon={<MemoryIcon sx={{ fontSize: 32 }} />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <HealthCard
            title="CPU"
            status={health.components.cpu}
            icon={<SpeedIcon sx={{ fontSize: 32 }} />}
          />
        </Grid>
      </Grid>

      {/* System Metrics */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Metrics
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Uptime
                  </Typography>
                  <Typography variant="h6">
                    {Math.floor(health.metrics.uptime / 86400)} days
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Active Connections
                  </Typography>
                  <Typography variant="h6">
                    {health.metrics.activeConnections}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Queue Size
                  </Typography>
                  <Typography variant="h6">
                    {health.metrics.queueSize}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average Response Time
                  </Typography>
                  <Typography variant="h6">
                    {health.metrics.averageResponseTime}ms
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Error Rate
                  </Typography>
                  <Typography variant="h6">
                    {(health.metrics.errorRate * 100).toFixed(2)}%
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Resource Usage
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Memory Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={78}
                    color="warning"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">78% used</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    CPU Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={45}
                    color="success"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">45% used</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Storage Usage
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={62}
                    color="primary"
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Typography variant="caption">62% used</Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Component Details */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Component Details
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Component</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Message</TableCell>
                      <TableCell>Last Check</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(health.components).map(([key, component]) => (
                      <TableRow key={key}>
                        <TableCell>
                          <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                            {key}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <StatusChip status={component.status} />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {component.message}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatRelativeTime(component.lastCheck)}
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