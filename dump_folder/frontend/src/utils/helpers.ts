/**
 * General utility functions
 */

import { format, formatDistance, parseISO } from 'date-fns';

/**
 * Format date string
 */
export const formatDate = (dateString: string, pattern = 'MMM dd, yyyy'): string => {
  return format(parseISO(dateString), pattern);
};

/**
 * Format date and time
 */
export const formatDateTime = (dateString: string): string => {
  return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
};

/**
 * Format relative time
 */
export const formatRelativeTime = (dateString: string): string => {
  return formatDistance(parseISO(dateString), new Date(), { addSuffix: true });
};

/**
 * Capitalize first letter
 */
export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1);
};

/**
 * Truncate text
 */
export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};

/**
 * Get status color
 */
export const getStatusColor = (status: string): string => {
  const statusColors: Record<string, string> = {
    // Server statuses
    active: 'success',
    inactive: 'error',
    maintenance: 'warning',
    
    // Job statuses
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'error',
    cancelled: 'default',
    
    // Approval statuses
    approved: 'success',
    rejected: 'error',
    expired: 'default',
    
    // Health statuses
    healthy: 'success',
    warning: 'warning',
    critical: 'error',
    
    // Connectivity
    connected: 'success',
    disconnected: 'error',
    unknown: 'default',
  };
  
  return statusColors[status] || 'default';
};

/**
 * Get OS icon
 */
export const getOSIcon = (os: string): string => {
  const osIcons: Record<string, string> = {
    ubuntu: '🐧',
    debian: '🐧',
    centos: '🔴',
    rhel: '🔴',
    fedora: '🔵',
  };
  
  return osIcons[os] || '💻';
};

/**
 * Get environment color
 */
export const getEnvironmentColor = (env: string): string => {
  const envColors: Record<string, string> = {
    production: 'error',
    staging: 'warning',
    development: 'info',
    testing: 'default',
  };
  
  return envColors[env] || 'default';
};

/**
 * Calculate success rate
 */
export const calculateSuccessRate = (total: number, failed: number): number => {
  if (total === 0) return 0;
  return Math.round(((total - failed) / total) * 100);
};

/**
 * Format bytes
 */
export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format duration
 */
export const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
};

/**
 * Debounce function
 */
export const debounce = <T extends (...args: any[]) => void>(
  func: T,
  delay: number
): T => {
  let timeoutId: NodeJS.Timeout;
  
  return ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  }) as T;
};

/**
 * Generate random ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
};

/**
 * Download file
 */
export const downloadFile = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Copy to clipboard
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    const result = document.execCommand('copy');
    document.body.removeChild(textArea);
    return result;
  }
};

/**
 * Validate email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Get quarter from date
 */
export const getQuarter = (date: Date = new Date()): string => {
  const year = date.getFullYear();
  const quarter = Math.ceil((date.getMonth() + 1) / 3);
  return `Q${quarter}_${year}`;
};

/**
 * Parse CSV
 */
export const parseCSV = (csv: string): string[][] => {
  const lines = csv.split('\n');
  const result: string[][] = [];
  
  for (const line of lines) {
    if (line.trim()) {
      const row = line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''));
      result.push(row);
    }
  }
  
  return result;
};

/**
 * Convert to CSV
 */
export const toCSV = (data: any[]): string => {
  if (!data.length) return '';
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    ),
  ];
  
  return csvContent.join('\n');
};