/**
 * Dashboard page component
 */

import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  useTheme,
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Build as BuildIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';

import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { StatusChip } from '@/components/Common/StatusChip';
import { apiService } from '@/services/api';
import { formatRelativeTime, calculateSuccessRate } from '@/utils/helpers';
import { DashboardStats } from '@/types/api';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
}

const StatCard = ({ title, value, icon, color, subtitle }: StatCardProps) => (
  <Card>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box>
          <Typography variant="h4" component="div" color={color}>
            {value}
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary">
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ color, opacity: 0.7 }}>
          {icon}
        </Box>
      </Box>
    </CardContent>
  </Card>
);

export const Dashboard = () => {
  const theme = useTheme();

  // Fetch dashboard statistics
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const [statsResponse, healthResponse] = await Promise.all([
        apiService.getSystemStats(),
        apiService.getSystemHealth(),
      ]);
      
      return {
        stats: statsResponse.data,
        health: healthResponse.data,
      };
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">
          Error loading dashboard: {(error as Error).message}
        </Typography>
      </Box>
    );
  }

  const systemStats = stats?.stats;
  const systemHealth = stats?.health;

  const dashboardStats: DashboardStats = {
    serversTotal: systemStats?.servers?.total || 0,
    serversActive: systemStats?.servers?.active || 0,
    serversInactive: systemStats?.servers?.inactive || 0,
    jobsRunning: systemStats?.patching?.totalJobs || 0,
    jobsCompleted: systemStats?.patching?.completedJobs || 0,
    jobsFailed: systemStats?.patching?.failedJobs || 0,
    approvalsNeeded: systemStats?.approvals?.pending || 0,
    systemHealth: systemHealth?.overall || 'unknown',
    lastUpdate: new Date().toISOString(),
  };

  const patchingSuccessRate = calculateSuccessRate(
    dashboardStats.jobsCompleted + dashboardStats.jobsFailed,
    dashboardStats.jobsFailed
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Server Statistics */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Servers"
            value={dashboardStats.serversTotal}
            icon={<ComputerIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.primary.main}
            subtitle={`${dashboardStats.serversActive} active`}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Jobs"
            value={dashboardStats.jobsRunning}
            icon={<BuildIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.warning.main}
            subtitle="Currently running"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Success Rate"
            value={`${patchingSuccessRate}%`}
            icon={<TrendingUpIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.success.main}
            subtitle="Last 30 days"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Pending Approvals"
            value={dashboardStats.approvalsNeeded}
            icon={<ScheduleIcon sx={{ fontSize: 40 }} />}
            color={theme.palette.info.main}
            subtitle="Need attention"
          />
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <StatusChip status={systemHealth?.overall || 'unknown'} />
                <Typography variant="body2" color="text.secondary">
                  Last updated: {formatRelativeTime(dashboardStats.lastUpdate)}
                </Typography>
              </Box>
              
              <Grid container spacing={2}>
                {systemHealth?.components && Object.entries(systemHealth.components).map(([key, component]) => (
                  <Grid item xs={6} key={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {component.status === 'healthy' ? (
                        <CheckCircleIcon color="success" fontSize="small" />
                      ) : (
                        <ErrorIcon color="error" fontSize="small" />
                      )}
                      <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                        {key}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CheckCircleIcon color="success" fontSize="small" />
                  <Typography variant="body2">
                    5 servers patched successfully
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    2 hours ago
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ErrorIcon color="error" fontSize="small" />
                  <Typography variant="body2">
                    Patching failed on web-01
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    3 hours ago
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ScheduleIcon color="info" fontSize="small" />
                  <Typography variant="body2">
                    3 approval requests submitted
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    4 hours ago
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Environment Overview
              </Typography>
              <Grid container spacing={2}>
                {systemStats?.servers?.byEnvironment && Object.entries(systemStats.servers.byEnvironment).map(([env, count]) => (
                  <Grid item xs={6} sm={3} key={env}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {count}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                        {env}
                      </Typography>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};