/**
 * Application constants
 */

export const APP_NAME = 'Linux Patching Automation';
export const APP_VERSION = '1.0.0';

export const API_ENDPOINTS = {
  AUTH: '/auth',
  SERVERS: '/servers',
  PATCHING: '/patching',
  APPROVALS: '/approvals',
  REPORTS: '/reports',
  SYSTEM: '/system',
  AUDIT: '/audit',
  HEALTH: '/health',
  WEBSOCKET: '/ws',
} as const;

export const STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PROFILE: 'user_profile',
  THEME: 'theme',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  TABLE_SETTINGS: 'table_settings',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  SERVERS: '/servers',
  PATCHING: '/patching',
  APPROVALS: '/approvals',
  REPORTS: '/reports',
  SYSTEM: '/system',
  AUDIT: '/audit',
  PROFILE: '/profile',
  SETTINGS: '/settings',
} as const;

export const PERMISSIONS = {
  // Server permissions
  SERVERS_VIEW: 'servers.view',
  SERVERS_CREATE: 'servers.create',
  SERVERS_UPDATE: 'servers.update',
  SERVERS_DELETE: 'servers.delete',
  SERVERS_IMPORT: 'servers.import',
  SERVERS_EXPORT: 'servers.export',
  
  // Patching permissions
  PATCHING_VIEW: 'patching.view',
  PATCHING_START: 'patching.start',
  PATCHING_CANCEL: 'patching.cancel',
  PATCHING_ROLLBACK: 'patching.rollback',
  
  // Approval permissions
  APPROVALS_VIEW: 'approvals.view',
  APPROVALS_CREATE: 'approvals.create',
  APPROVALS_APPROVE: 'approvals.approve',
  APPROVALS_REJECT: 'approvals.reject',
  
  // Report permissions
  REPORTS_VIEW: 'reports.view',
  REPORTS_GENERATE: 'reports.generate',
  REPORTS_DOWNLOAD: 'reports.download',
  REPORTS_EMAIL: 'reports.email',
  
  // System permissions
  SYSTEM_VIEW: 'system.view',
  SYSTEM_CONFIGURE: 'system.configure',
  SYSTEM_HEALTH: 'system.health',
  
  // Audit permissions
  AUDIT_VIEW: 'audit.view',
  
  // User permissions
  USERS_VIEW: 'users.view',
  USERS_CREATE: 'users.create',
  USERS_UPDATE: 'users.update',
  USERS_DELETE: 'users.delete',
} as const;

export const ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
  VIEWER: 'viewer',
} as const;

export const OPERATING_SYSTEMS = [
  { value: 'ubuntu', label: 'Ubuntu' },
  { value: 'debian', label: 'Debian' },
  { value: 'centos', label: 'CentOS' },
  { value: 'rhel', label: 'Red Hat Enterprise Linux' },
  { value: 'fedora', label: 'Fedora' },
] as const;

export const ENVIRONMENTS = [
  { value: 'production', label: 'Production' },
  { value: 'staging', label: 'Staging' },
  { value: 'development', label: 'Development' },
  { value: 'testing', label: 'Testing' },
] as const;

export const QUARTERS = [
  { value: 'Q1', label: 'Q1' },
  { value: 'Q2', label: 'Q2' },
  { value: 'Q3', label: 'Q3' },
  { value: 'Q4', label: 'Q4' },
] as const;

export const SERVER_STATUSES = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'maintenance', label: 'Maintenance' },
] as const;

export const JOB_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
] as const;

export const APPROVAL_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'expired', label: 'Expired' },
] as const;

export const REPORT_TYPES = [
  { value: 'summary', label: 'Summary Report' },
  { value: 'detailed', label: 'Detailed Report' },
  { value: 'quarterly', label: 'Quarterly Report' },
  { value: 'daily', label: 'Daily Report' },
  { value: 'custom', label: 'Custom Report' },
] as const;

export const REPORT_FORMATS = [
  { value: 'pdf', label: 'PDF' },
  { value: 'csv', label: 'CSV' },
  { value: 'json', label: 'JSON' },
  { value: 'html', label: 'HTML' },
] as const;

export const NOTIFICATION_TYPES = [
  { value: 'info', label: 'Info' },
  { value: 'success', label: 'Success' },
  { value: 'warning', label: 'Warning' },
  { value: 'error', label: 'Error' },
] as const;

export const PAGINATION_SIZES = [10, 25, 50, 100] as const;

export const REFRESH_INTERVALS = {
  DASHBOARD: 30000, // 30 seconds
  SERVERS: 60000, // 1 minute
  PATCHING: 5000, // 5 seconds
  SYSTEM_HEALTH: 30000, // 30 seconds
} as const;

export const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney',
] as const;

export const VALIDATION_RULES = {
  SERVER_NAME: /^[a-zA-Z0-9\-_.]+$/,
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  IP_ADDRESS: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
  HOSTNAME: /^[a-zA-Z0-9\-_.]+$/,
  PORT: /^([1-9][0-9]{0,3}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])$/,
} as const;

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Session expired. Please login again.',
  FORBIDDEN: 'Access denied. You don\'t have permission for this action.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  UNKNOWN_ERROR: 'An unexpected error occurred.',
} as const;

export const SUCCESS_MESSAGES = {
  SERVER_CREATED: 'Server created successfully.',
  SERVER_UPDATED: 'Server updated successfully.',
  SERVER_DELETED: 'Server deleted successfully.',
  PATCHING_STARTED: 'Patching job started successfully.',
  PATCHING_CANCELLED: 'Patching job cancelled successfully.',
  APPROVAL_SUBMITTED: 'Approval request submitted successfully.',
  APPROVAL_APPROVED: 'Servers approved successfully.',
  APPROVAL_REJECTED: 'Servers rejected successfully.',
  REPORT_GENERATED: 'Report generated successfully.',
  SETTINGS_SAVED: 'Settings saved successfully.',
} as const;

export const THEME_COLORS = {
  primary: '#1976d2',
  secondary: '#dc004e',
  success: '#2e7d32',
  warning: '#ed6c02',
  error: '#d32f2f',
  info: '#0288d1',
} as const;

export const CHART_COLORS = [
  '#1976d2',
  '#dc004e',
  '#2e7d32',
  '#ed6c02',
  '#9c27b0',
  '#f57c00',
  '#0288d1',
  '#5d4037',
  '#616161',
  '#ad1457',
] as const;