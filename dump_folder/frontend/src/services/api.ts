/**
 * API Service Layer
 * Handles all backend communication with proper error handling and security
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';

import { getAuthToken, removeAuthToken } from '@/utils/auth';
import { 
  ApiResponse, 
  AuthTokens, 
  LoginCredentials, 
  Server, 
  PatchingJob, 
  ApprovalRequest,
  PreCheckResult,
  PatchingStatus,
  SystemHealth,
  ReportConfig,
  UserProfile,
  PaginatedResponse,
  ApiError,
} from '@/types/api';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
    this.timeout = 30000; // 30 seconds

    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: this.timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * Setup request/response interceptors
   */
  private setupInterceptors(): void {
    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        const token = getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracing
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        // Add timestamp
        config.headers['X-Timestamp'] = new Date().toISOString();

        return config;
      },
      (error) => {
        return Promise.reject(this.handleError(error));
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        // Handle 401 - Unauthorized
        if (error.response?.status === 401) {
          removeAuthToken();
          window.location.href = '/login';
          return Promise.reject(new Error('Session expired. Please login again.'));
        }

        // Handle 403 - Forbidden
        if (error.response?.status === 403) {
          toast.error('Access denied. You don\'t have permission for this action.');
        }

        // Handle 500 - Internal Server Error
        if (error.response?.status >= 500) {
          toast.error('Server error. Please try again later.');
        }

        return Promise.reject(this.handleError(error));
      }
    );
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Handle API errors
   */
  private handleError(error: any): ApiError {
    if (error.response) {
      // Server responded with error status
      return {
        message: error.response.data?.message || error.message,
        status: error.response.status,
        code: error.response.data?.code || 'UNKNOWN_ERROR',
        details: error.response.data?.details || null,
        timestamp: new Date().toISOString(),
      };
    } else if (error.request) {
      // Request was made but no response received
      return {
        message: 'Network error. Please check your connection.',
        status: 0,
        code: 'NETWORK_ERROR',
        details: null,
        timestamp: new Date().toISOString(),
      };
    } else {
      // Something else happened
      return {
        message: error.message || 'An unexpected error occurred',
        status: 0,
        code: 'UNKNOWN_ERROR',
        details: null,
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Make API request with proper error handling
   */
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.api.request<ApiResponse<T>>(config);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // ===== AUTHENTICATION METHODS =====

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthTokens>> {
    return this.request<AuthTokens>({
      method: 'POST',
      url: '/auth/login',
      data: credentials,
    });
  }

  /**
   * Refresh authentication token
   */
  async refreshToken(refreshToken: string): Promise<ApiResponse<AuthTokens>> {
    return this.request<AuthTokens>({
      method: 'POST',
      url: '/auth/refresh',
      data: { refresh_token: refreshToken },
    });
  }

  /**
   * Logout user
   */
  async logout(): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/auth/logout',
    });
  }

  /**
   * Get user profile
   */
  async getUserProfile(): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>({
      method: 'GET',
      url: '/auth/profile',
    });
  }

  // ===== SERVER MANAGEMENT METHODS =====

  /**
   * Get all servers with pagination and filtering
   */
  async getServers(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    group?: string;
    environment?: string;
    status?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<ApiResponse<PaginatedResponse<Server>>> {
    return this.request<PaginatedResponse<Server>>({
      method: 'GET',
      url: '/servers',
      params,
    });
  }

  /**
   * Get server by ID
   */
  async getServer(id: string): Promise<ApiResponse<Server>> {
    return this.request<Server>({
      method: 'GET',
      url: `/servers/${id}`,
    });
  }

  /**
   * Create new server
   */
  async createServer(server: Partial<Server>): Promise<ApiResponse<Server>> {
    return this.request<Server>({
      method: 'POST',
      url: '/servers',
      data: server,
    });
  }

  /**
   * Update server
   */
  async updateServer(id: string, updates: Partial<Server>): Promise<ApiResponse<Server>> {
    return this.request<Server>({
      method: 'PUT',
      url: `/servers/${id}`,
      data: updates,
    });
  }

  /**
   * Delete server
   */
  async deleteServer(id: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'DELETE',
      url: `/servers/${id}`,
    });
  }

  /**
   * Test server connectivity
   */
  async testServerConnectivity(serverId: string): Promise<ApiResponse<{ connected: boolean; message: string; responseTime: number }>> {
    return this.request<{ connected: boolean; message: string; responseTime: number }>({
      method: 'POST',
      url: `/servers/${serverId}/test`,
    });
  }

  /**
   * Import servers from CSV
   */
  async importServers(file: File): Promise<ApiResponse<{ imported: number; errors: string[] }>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<{ imported: number; errors: string[] }>({
      method: 'POST',
      url: '/servers/import',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  /**
   * Export servers to CSV
   */
  async exportServers(filters?: any): Promise<Blob> {
    const response = await this.api.request({
      method: 'GET',
      url: '/servers/export',
      params: filters,
      responseType: 'blob',
    });
    return response.data;
  }

  // ===== PATCHING METHODS =====

  /**
   * Get patching status
   */
  async getPatchingStatus(quarter?: string): Promise<ApiResponse<PatchingStatus>> {
    return this.request<PatchingStatus>({
      method: 'GET',
      url: '/patching/status',
      params: { quarter },
    });
  }

  /**
   * Start patching job
   */
  async startPatching(config: {
    servers: string[];
    quarter?: string;
    dryRun?: boolean;
    force?: boolean;
    skipPrecheck?: boolean;
    skipPostcheck?: boolean;
  }): Promise<ApiResponse<PatchingJob>> {
    return this.request<PatchingJob>({
      method: 'POST',
      url: '/patching/start',
      data: config,
    });
  }

  /**
   * Get patching job details
   */
  async getPatchingJob(jobId: string): Promise<ApiResponse<PatchingJob>> {
    return this.request<PatchingJob>({
      method: 'GET',
      url: `/patching/jobs/${jobId}`,
    });
  }

  /**
   * Get all patching jobs
   */
  async getPatchingJobs(params?: {
    page?: number;
    pageSize?: number;
    status?: string;
    quarter?: string;
    server?: string;
  }): Promise<ApiResponse<PaginatedResponse<PatchingJob>>> {
    return this.request<PaginatedResponse<PatchingJob>>({
      method: 'GET',
      url: '/patching/jobs',
      params,
    });
  }

  /**
   * Cancel patching job
   */
  async cancelPatchingJob(jobId: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: `/patching/jobs/${jobId}/cancel`,
    });
  }

  /**
   * Rollback server
   */
  async rollbackServer(serverId: string, reason: string): Promise<ApiResponse<PatchingJob>> {
    return this.request<PatchingJob>({
      method: 'POST',
      url: `/patching/rollback`,
      data: { server_id: serverId, reason },
    });
  }

  // ===== PRE-CHECK METHODS =====

  /**
   * Run pre-checks
   */
  async runPreChecks(servers: string[], quarter?: string): Promise<ApiResponse<PreCheckResult[]>> {
    return this.request<PreCheckResult[]>({
      method: 'POST',
      url: '/precheck/run',
      data: { servers, quarter },
    });
  }

  /**
   * Get pre-check results
   */
  async getPreCheckResults(params?: {
    server?: string;
    quarter?: string;
    status?: string;
  }): Promise<ApiResponse<PreCheckResult[]>> {
    return this.request<PreCheckResult[]>({
      method: 'GET',
      url: '/precheck/results',
      params,
    });
  }

  // ===== APPROVAL METHODS =====

  /**
   * Get approval requests
   */
  async getApprovalRequests(params?: {
    status?: string;
    quarter?: string;
    page?: number;
    pageSize?: number;
  }): Promise<ApiResponse<PaginatedResponse<ApprovalRequest>>> {
    return this.request<PaginatedResponse<ApprovalRequest>>({
      method: 'GET',
      url: '/approvals',
      params,
    });
  }

  /**
   * Create approval request
   */
  async createApprovalRequest(request: Partial<ApprovalRequest>): Promise<ApiResponse<ApprovalRequest>> {
    return this.request<ApprovalRequest>({
      method: 'POST',
      url: '/approvals',
      data: request,
    });
  }

  /**
   * Approve servers
   */
  async approveServers(approvalIds: string[], comment?: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/approvals/approve',
      data: { approval_ids: approvalIds, comment },
    });
  }

  /**
   * Reject servers
   */
  async rejectServers(approvalIds: string[], reason: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/approvals/reject',
      data: { approval_ids: approvalIds, reason },
    });
  }

  // ===== REPORTING METHODS =====

  /**
   * Generate report
   */
  async generateReport(config: ReportConfig): Promise<ApiResponse<{ reportId: string; downloadUrl: string }>> {
    return this.request<{ reportId: string; downloadUrl: string }>({
      method: 'POST',
      url: '/reports/generate',
      data: config,
    });
  }

  /**
   * Get report
   */
  async getReport(reportId: string): Promise<Blob> {
    const response = await this.api.request({
      method: 'GET',
      url: `/reports/${reportId}`,
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Email report
   */
  async emailReport(reportId: string, recipients: string[]): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: `/reports/${reportId}/email`,
      data: { recipients },
    });
  }

  // ===== SYSTEM METHODS =====

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<ApiResponse<SystemHealth>> {
    return this.request<SystemHealth>({
      method: 'GET',
      url: '/system/health',
    });
  }

  /**
   * Get system statistics
   */
  async getSystemStats(): Promise<ApiResponse<any>> {
    return this.request<any>({
      method: 'GET',
      url: '/system/stats',
    });
  }

  /**
   * Test email configuration
   */
  async testEmail(recipient: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/system/test-email',
      data: { recipient },
    });
  }

  /**
   * Get audit logs
   */
  async getAuditLogs(params?: {
    page?: number;
    pageSize?: number;
    startDate?: string;
    endDate?: string;
    action?: string;
    user?: string;
  }): Promise<ApiResponse<PaginatedResponse<any>>> {
    return this.request<PaginatedResponse<any>>({
      method: 'GET',
      url: '/audit/logs',
      params,
    });
  }

  // ===== WEBSOCKET METHODS =====

  /**
   * Get WebSocket connection URL
   */
  getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = this.baseURL.replace(/^https?:\/\//, '');
    return `${protocol}//${host}/ws`;
  }

  // ===== UTILITY METHODS =====

  /**
   * Upload file
   */
  async uploadFile(file: File, endpoint: string, onProgress?: (progress: number) => void): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    return this.request<any>({
      method: 'POST',
      url: endpoint,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
  }

  /**
   * Download file
   */
  async downloadFile(url: string, filename?: string): Promise<void> {
    const response = await this.api.request({
      method: 'GET',
      url,
      responseType: 'blob',
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      await this.request<any>({
        method: 'GET',
        url: '/health',
        timeout: 5000,
      });
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;