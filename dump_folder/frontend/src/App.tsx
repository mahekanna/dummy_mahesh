/**
 * Main App component
 */

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { Toaster } from 'react-hot-toast';

import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { MainLayout } from '@/components/Layout/MainLayout';
import { Dashboard } from '@/pages/Dashboard/Dashboard';
import { ServerList } from '@/pages/Servers/ServerList';
import { Login } from '@/pages/Login/Login';
import { PatchingJobs } from '@/pages/Patching/PatchingJobs';
import { ApprovalList } from '@/pages/Approvals/ApprovalList';
import { ReportGenerator } from '@/pages/Reports/ReportGenerator';
import { SystemHealth } from '@/pages/System/SystemHealth';
import { useAuth } from '@/hooks/useAuth';
import { ROUTES } from '@/constants';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30000, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
  },
});

// Protected Route Component
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <MainLayout>{children}</MainLayout>;
};

// App Routes
const AppRoutes = () => {
  return (
    <Routes>
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route
        path={ROUTES.DASHBOARD}
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.SERVERS}
        element={
          <ProtectedRoute>
            <ServerList />
          </ProtectedRoute>
        }
      />
      <Route
        path={`${ROUTES.PATCHING}/jobs`}
        element={
          <ProtectedRoute>
            <PatchingJobs />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.APPROVALS}
        element={
          <ProtectedRoute>
            <ApprovalList />
          </ProtectedRoute>
        }
      />
      <Route
        path={ROUTES.REPORTS}
        element={
          <ProtectedRoute>
            <ReportGenerator />
          </ProtectedRoute>
        }
      />
      <Route
        path={`${ROUTES.SYSTEM}/health`}
        element={
          <ProtectedRoute>
            <SystemHealth />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
      <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
    </Routes>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <AppRoutes />
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;