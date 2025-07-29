/**
 * Authentication hook
 */

import { useCallback, useContext, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';

import { apiService } from '@/services/api';
import { 
  getAuthToken, 
  setAuthToken, 
  setRefreshToken, 
  setUserProfile, 
  removeAuthToken, 
  isAuthenticated,
  getUserProfile,
} from '@/utils/auth';
import { LoginCredentials, UserProfile, AuthTokens } from '@/types/api';

interface AuthState {
  isAuthenticated: boolean;
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
}

export const useAuth = () => {
  const queryClient = useQueryClient();
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: isAuthenticated(),
    user: getUserProfile(),
    loading: false,
    error: null,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (credentials: LoginCredentials) => apiService.login(credentials),
    onSuccess: (response) => {
      const { accessToken, refreshToken } = response.data;
      setAuthToken(accessToken);
      setRefreshToken(refreshToken);
      
      // Fetch user profile after successful login
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      toast.success('Login successful');
    },
    onError: (error: any) => {
      setAuthState(prev => ({ ...prev, error: error.message }));
      toast.error(error.message || 'Login failed');
    },
  });

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: () => apiService.logout(),
    onSuccess: () => {
      removeAuthToken();
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      });
      queryClient.clear();
      toast.success('Logged out successfully');
    },
    onError: (error: any) => {
      // Even if logout fails on server, clear local auth
      removeAuthToken();
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      });
      queryClient.clear();
      toast.error(error.message || 'Logout failed');
    },
  });

  // User profile query
  const { data: userProfile, isLoading: profileLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: () => apiService.getUserProfile(),
    enabled: isAuthenticated(),
    retry: false,
    onSuccess: (response) => {
      const profile = response.data;
      setUserProfile(profile);
      setAuthState(prev => ({
        ...prev,
        user: profile,
        isAuthenticated: true,
      }));
    },
    onError: () => {
      // If profile fetch fails, user is likely not authenticated
      removeAuthToken();
      setAuthState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      });
    },
  });

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    setAuthState(prev => ({ ...prev, loading: true, error: null }));
    await loginMutation.mutateAsync(credentials);
  }, [loginMutation]);

  // Logout function
  const logout = useCallback(async () => {
    setAuthState(prev => ({ ...prev, loading: true }));
    await logoutMutation.mutateAsync();
  }, [logoutMutation]);

  // Check if user has permission
  const hasPermission = useCallback((permission: string): boolean => {
    return authState.user?.permissions?.includes(permission) || false;
  }, [authState.user]);

  // Check if user has role
  const hasRole = useCallback((role: string): boolean => {
    return authState.user?.role === role;
  }, [authState.user]);

  // Check if user is admin
  const isAdmin = useCallback((): boolean => {
    return hasRole('admin');
  }, [hasRole]);

  // Check if user is operator
  const isOperator = useCallback((): boolean => {
    return hasRole('operator') || hasRole('admin');
  }, [hasRole]);

  // Update loading state
  useEffect(() => {
    setAuthState(prev => ({ 
      ...prev, 
      loading: loginMutation.isPending || logoutMutation.isPending || profileLoading,
    }));
  }, [loginMutation.isPending, logoutMutation.isPending, profileLoading]);

  return {
    ...authState,
    login,
    logout,
    hasPermission,
    hasRole,
    isAdmin,
    isOperator,
    refetch: () => queryClient.invalidateQueries({ queryKey: ['user-profile'] }),
  };
};