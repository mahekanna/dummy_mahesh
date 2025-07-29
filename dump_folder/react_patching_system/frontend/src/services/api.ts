/**
 * API Service Layer - Converted from Flask app functionality
 * Handles all backend communication with the new React Patching System API
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  total?: number;
  currentQuarter?: string;
}

export interface AuthTokens {
  token: string;
  user: UserProfile;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface UserProfile {
  email: string;
  name: string;
  role: string;
  permissions: string[];
  auth_method?: string;
  department?: string;
  title?: string;
}

export interface Server {
  id: string;
  serverName: string;
  hostGroup: string;
  environment: string;
  primaryOwner: string;
  secondaryOwner: string;
  location: string;
  incidentTicket: string;
  patcherEmail: string;
  serverTimezone: string;
  operatingSystem: string;
  q1PatchDate: string;
  q1PatchTime: string;
  q1ApprovalStatus: string;
  q2PatchDate: string;
  q2PatchTime: string;
  q2ApprovalStatus: string;
  q3PatchDate: string;
  q3PatchTime: string;
  q3ApprovalStatus: string;
  q4PatchDate: string;
  q4PatchTime: string;
  q4ApprovalStatus: string;
  currentQuarterStatus: string;
}

export interface QuarterInfo {
  id: string;
  name: string;
  months: number[];
  is_current: boolean;
  description: string;
}

export interface TimezoneInfo {
  success: boolean;
  timezone: string;
  abbreviation: string;
  current_time: string;
  offset: string;
}

export interface AIRecommendation {
  success: boolean;
  recommended_date: string;
  recommended_time: string;
  confidence_level: string;
  reasoning: string[];
  risk_factors: string[];
  alternative_times: string[];
  message?: string;
}

export interface SystemHealth {
  success: boolean;
  health: {
    status: string;
    message: string;
    details: {
      disk_space_gb: number;
      csv_accessible: boolean;
      ldap_status: string;
      timestamp: string;
    };
  };
}

export interface SystemStats {
  success: boolean;
  stats: {
    overview: {
      total_servers: number;
      pending: number;
      approved: number;
      scheduled: number;
      completed: number;
      failed: number;
    };
    host_groups: { [key: string]: number };
    environments: { [key: string]: number };
    current_quarter: string;
    quarter_info: any;
    timestamp: string;
  };
}

export interface ReportData {
  success: boolean;
  report_data: {
    host_group_breakdown: { [key: string]: any };
    timeline_data: {
      labels: string[];
      completed: number[];
      scheduled: number[];
    };
    attention_required: Array<{
      server: string;
      issue: string;
      owner: string;
      status: string;
      priority: string;
    }>;
    completed_servers: Array<{
      server_name: string;
      host_group: string;
      patch_date: string;
      patch_time: string;
      completion_date: string;
      duration: string;
      owner: string;
      status: string;
    }>;
  };
}

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;
  private timeout: number;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8002';
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
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request ID for tracing
        config.headers['X-Request-ID'] = this.generateRequestId();
        config.headers['X-Timestamp'] = new Date().toISOString();

        return config;
      },
      (error) => {
        return Promise.reject(error);
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
          this.removeAuthToken();
          window.location.href = '/login';
          return Promise.reject(new Error('Session expired. Please login again.'));
        }

        // Handle 403 - Forbidden
        if (error.response?.status === 403) {
          console.error('Access denied');
        }

        // Handle 500 - Internal Server Error
        if (error.response?.status >= 500) {
          console.error('Server error');
        }

        return Promise.reject(error);
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
   * Get auth token from localStorage
   */
  private getAuthToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * Store auth token in localStorage
   */
  private setAuthToken(token: string): void {
    localStorage.setItem('auth_token', token);
  }

  /**
   * Remove auth token from localStorage
   */
  private removeAuthToken(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_profile');
  }

  /**
   * Make API request with proper error handling
   */
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await this.api.request<ApiResponse<T>>(config);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.message || error.message || 'API request failed');
    }
  }

  // ===== AUTHENTICATION METHODS =====

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthTokens>> {
    const response = await this.request<AuthTokens>({
      method: 'POST',
      url: '/api/auth/login',
      data: credentials,
    });

    if (response.success && response.data) {
      this.setAuthToken(response.data.token);
      localStorage.setItem('user_profile', JSON.stringify(response.data.user));
    }

    return response;
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    this.removeAuthToken();
  }

  /**
   * Get user profile
   */
  async getUserProfile(): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>({
      method: 'GET',
      url: '/api/auth/profile',
    });
  }

  /**
   * Get stored user profile
   */
  getStoredUserProfile(): UserProfile | null {
    const profile = localStorage.getItem('user_profile');
    return profile ? JSON.parse(profile) : null;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAuthToken();
  }

  // ===== SERVER MANAGEMENT METHODS =====

  /**
   * Get all servers
   */
  async getServers(): Promise<ApiResponse<Server[]>> {
    return this.request<Server[]>({
      method: 'GET',
      url: '/api/servers',
    });
  }

  /**
   * Get server by name
   */
  async getServer(serverName: string): Promise<ApiResponse<Server>> {
    return this.request<Server>({
      method: 'GET',
      url: `/api/servers/${encodeURIComponent(serverName)}`,
    });
  }

  /**
   * Update server schedule
   */
  async updateServerSchedule(
    serverName: string,
    scheduleData: {
      quarter: string;
      patchDate: string;
      patchTime: string;
    }
  ): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'PUT',
      url: `/api/servers/${encodeURIComponent(serverName)}/schedule`,
      data: scheduleData,
    });
  }

  /**
   * Approve server schedule
   */
  async approveServerSchedule(
    serverName: string,
    quarter?: string
  ): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: `/api/servers/${encodeURIComponent(serverName)}/approve`,
      data: { quarter },
    });
  }

  /**
   * Update server info (incident ticket, patcher email)
   */
  async updateServerInfo(
    serverName: string,
    infoData: {
      incidentTicket?: string;
      patcherEmail?: string;
    }
  ): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'PUT',
      url: `/api/servers/${encodeURIComponent(serverName)}/info`,
      data: infoData,
    });
  }

  // ===== UTILITY METHODS =====

  /**
   * Get available dates for a quarter
   */
  async getAvailableDates(quarter: string): Promise<ApiResponse<string[]>> {
    return this.request<string[]>({
      method: 'GET',
      url: `/api/utils/available-dates/${quarter}`,
    });
  }

  /**
   * Get server timezone information
   */
  async getServerTimezone(serverName: string): Promise<TimezoneInfo> {
    const response = await this.api.get<TimezoneInfo>(
      `/api/utils/server-timezone/${encodeURIComponent(serverName)}`
    );
    return response.data;
  }

  /**
   * Get AI recommendation for server scheduling
   */
  async getAIRecommendation(serverName: string, quarter: string): Promise<AIRecommendation> {
    const response = await this.api.get<AIRecommendation>(
      `/api/utils/ai-recommendation/${encodeURIComponent(serverName)}/${quarter}`
    );
    return response.data;
  }

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.api.get<SystemHealth>('/api/utils/system/health');
    return response.data;
  }

  /**
   * Get system statistics
   */
  async getSystemStats(): Promise<SystemStats> {
    const response = await this.api.get<SystemStats>('/api/utils/system/stats');
    return response.data;
  }

  /**
   * Get quarters information
   */
  async getQuartersInfo(): Promise<ApiResponse<{ current_quarter: string; quarters: { [key: string]: QuarterInfo } }>> {
    return this.request<{ current_quarter: string; quarters: { [key: string]: QuarterInfo } }>({
      method: 'GET',
      url: '/api/utils/quarters',
    });
  }

  // ===== REPORTS METHODS =====

  /**
   * Get reports dashboard data
   */
  async getReportsData(params?: {
    type?: string;
    quarter?: string;
    host_group?: string;
    status?: string;
  }): Promise<ReportData> {
    const response = await this.api.get<ReportData>('/api/reports/dashboard', { params });
    return response.data;
  }

  /**
   * Export CSV report
   */
  async exportCSVReport(params: {
    type: string;
    quarter?: string;
    host_group?: string;
    status?: string;
    format?: string;
  }): Promise<Blob> {
    const response = await this.api.get('/api/reports/csv', {
      params: { ...params, format: 'download' },
      responseType: 'blob',
    });
    return response.data;
  }

  // ===== ADMIN METHODS =====

  /**
   * Generate admin report
   */
  async generateAdminReport(reportType: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: `/api/admin/reports/generate/${reportType}`,
    });
  }

  /**
   * Sync database
   */
  async syncDatabase(): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/api/admin/database/sync',
    });
  }

  /**
   * Run intelligent scheduling
   */
  async runIntelligentScheduling(): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/api/admin/scheduling/intelligent',
    });
  }

  /**
   * Test email configuration
   */
  async testEmail(recipient: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'POST',
      url: '/api/utils/test-email',
      data: { recipient },
    });
  }

  /**
   * Check API health
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.api.get('/api/health', { timeout: 5000 });
      return response.data.success === true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;