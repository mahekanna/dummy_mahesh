/**
 * Authentication utilities
 * Handles token management and user authentication
 */

import { UserProfile } from '@/types/api';

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_PROFILE_KEY = 'user_profile';

/**
 * Get authentication token from localStorage
 */
export const getAuthToken = (): string | null => {
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

/**
 * Set authentication token in localStorage
 */
export const setAuthToken = (token: string): void => {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
};

/**
 * Get refresh token from localStorage
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Set refresh token in localStorage
 */
export const setRefreshToken = (token: string): void => {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
};

/**
 * Get user profile from localStorage
 */
export const getUserProfile = (): UserProfile | null => {
  const profile = localStorage.getItem(USER_PROFILE_KEY);
  return profile ? JSON.parse(profile) : null;
};

/**
 * Set user profile in localStorage
 */
export const setUserProfile = (profile: UserProfile): void => {
  localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(profile));
};

/**
 * Remove authentication tokens and user profile
 */
export const removeAuthToken = (): void => {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_PROFILE_KEY);
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = getAuthToken();
  return !!token;
};

/**
 * Check if user has specific permission
 */
export const hasPermission = (permission: string): boolean => {
  const profile = getUserProfile();
  return profile?.permissions?.includes(permission) || false;
};

/**
 * Check if user has specific role
 */
export const hasRole = (role: string): boolean => {
  const profile = getUserProfile();
  return profile?.role === role;
};

/**
 * Check if user is admin
 */
export const isAdmin = (): boolean => {
  return hasRole('admin');
};

/**
 * Check if user is operator
 */
export const isOperator = (): boolean => {
  return hasRole('operator') || hasRole('admin');
};

/**
 * Check if token is expired
 */
export const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch {
    return true;
  }
};