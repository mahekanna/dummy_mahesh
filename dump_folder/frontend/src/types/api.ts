/**
 * API Types and Interfaces
 * Defines all TypeScript interfaces for API communication
 */

// ===== COMMON TYPES =====

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
  requestId?: string;
}

export interface ApiError {
  message: string;
  status: number;
  code: string;
  details?: any;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// ===== AUTHENTICATION TYPES =====

export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  scope?: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'operator' | 'viewer';
  permissions: string[];
  createdAt: string;
  updatedAt: string;
  lastLogin?: string;
  isActive: boolean;
  avatar?: string;
}

// ===== SERVER TYPES =====

export interface Server {
  id: string;
  serverName: string;
  hostGroup: string;
  operatingSystem: 'ubuntu' | 'debian' | 'centos' | 'rhel' | 'fedora';
  environment: 'production' | 'staging' | 'development' | 'testing';
  serverTimezone: string;
  location: string;
  primaryOwner: string;
  secondaryOwner?: string;
  primaryLinuxUser: string;
  secondaryLinuxUser?: string;
  patcherEmail: string;
  engineeringDomain?: string;
  incidentTicket?: string;
  
  // Patching Schedule
  q1PatchDate?: string;
  q1PatchTime?: string;
  q1ApprovalStatus: 'pending' | 'approved' | 'rejected';
  q2PatchDate?: string;
  q2PatchTime?: string;
  q2ApprovalStatus: 'pending' | 'approved' | 'rejected';
  q3PatchDate?: string;
  q3PatchTime?: string;
  q3ApprovalStatus: 'pending' | 'approved' | 'rejected';
  q4PatchDate?: string;
  q4PatchTime?: string;
  q4ApprovalStatus: 'pending' | 'approved' | 'rejected';
  
  // Status
  currentQuarterPatchingStatus: 'pending' | 'scheduled' | 'in_progress' | 'completed' | 'failed' | 'rolled_back';
  activeStatus: 'active' | 'inactive' | 'maintenance';
  lastSyncDate?: string;
  syncStatus: 'success' | 'failed' | 'pending';
  
  // SSH Configuration
  sshKeyPath?: string;
  sshPort: number;
  sudoUser?: string;
  
  // Patching Configuration
  backupRequired: boolean;
  rollbackPlan?: string;
  criticalServices: string[];
  maintenanceWindow?: string;
  patchGroupPriority: number;
  autoApprove: boolean;
  notificationEmail?: string;
  
  // Timestamps
  createdDate: string;
  modifiedDate: string;
  
  // Computed fields
  nextPatchDate?: string;
  daysSinceLastPatch?: number;
  connectivityStatus?: 'connected' | 'disconnected' | 'unknown';
  lastConnectivityCheck?: string;
}

// ===== PATCHING TYPES =====

export interface PatchingJob {
  id: string;
  name: string;
  description?: string;
  type: 'single' | 'batch' | 'rollback';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  
  // Configuration
  quarter?: string;
  servers: string[];
  dryRun: boolean;
  force: boolean;
  skipPrecheck: boolean;
  skipPostcheck: boolean;
  
  // Execution details
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  operator: string;
  
  // Results
  successCount: number;
  failureCount: number;
  totalCount: number;
  
  // Server results
  serverResults: PatchingServerResult[];
  
  // Metadata
  createdAt: string;
  updatedAt: string;
  
  // Logs
  logs: PatchingLog[];
}

export interface PatchingServerResult {
  serverId: string;
  serverName: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  patchesApplied: number;
  rebootRequired: boolean;
  rebootCompleted: boolean;
  preCheckStatus: 'passed' | 'failed' | 'skipped';
  postCheckStatus: 'passed' | 'failed' | 'skipped';
  errorMessage?: string;
  rollbackStatus?: 'success' | 'failed' | 'not_required';
  rollbackReason?: string;
}

export interface PatchingLog {
  id: string;
  jobId: string;
  serverId?: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  metadata?: any;
}

export interface PatchingStatus {
  currentQuarter: string;
  totalServers: number;
  pendingApproval: number;
  approved: number;
  scheduled: number;
  inProgress: number;
  completed: number;
  failed: number;
  rolledBack: number;
  successRate: number;
  activeOperations: number;
  lastUpdated: string;
  
  // Quarterly breakdown
  quarterlyStats: {
    [quarter: string]: {
      total: number;
      completed: number;
      failed: number;
      pending: number;
      successRate: number;
    };
  };
  
  // Group breakdown
  groupStats: {
    [group: string]: {
      total: number;
      completed: number;
      failed: number;
      pending: number;
      successRate: number;
    };
  };
}

// ===== PRE-CHECK TYPES =====

export interface PreCheckResult {
  id: string;
  serverId: string;
  serverName: string;
  quarter: string;
  checkType: string;
  checkName: string;
  status: 'passed' | 'failed' | 'warning';
  value?: string;
  threshold?: string;
  message: string;
  severity: 'low' | 'medium' | 'high';
  recommendation?: string;
  autoFixable: boolean;
  fixed: boolean;
  operator: string;
  duration: number;
  retryCount: number;
  lastRetry?: string;
  dependenciesMet: boolean;
  businessImpact: string;
  technicalImpact: string;
  resolutionSteps?: string[];
  escalationRequired: boolean;
  ownerNotified: boolean;
  timestamp: string;
}

export interface PreCheckSummary {
  serverId: string;
  serverName: string;
  overallStatus: 'passed' | 'failed' | 'warning';
  totalChecks: number;
  passedChecks: number;
  failedChecks: number;
  warningChecks: number;
  issues: PreCheckIssue[];
  timestamp: string;
}

export interface PreCheckIssue {
  check: string;
  issue: string;
  severity: 'low' | 'medium' | 'high';
  details: string;
  recommendation: string;
  autoFixable: boolean;
}

// ===== APPROVAL TYPES =====

export interface ApprovalRequest {
  id: string;
  serverId: string;
  serverName: string;
  quarter: string;
  requestedBy: string;
  requestDate: string;
  approver?: string;
  approvalDate?: string;
  status: 'pending' | 'approved' | 'rejected' | 'expired';
  approvalType: 'individual' | 'group' | 'batch' | 'auto';
  businessJustification: string;
  riskAssessment: string;
  rollbackPlan: string;
  notificationList: string[];
  emergencyContact: string;
  maintenanceWindow: string;
  dependencies: string[];
  testingRequired: boolean;
  backupRequired: boolean;
  changeRequestId?: string;
  comments?: string;
  autoApproved: boolean;
  expiryDate?: string;
  createdAt: string;
  updatedAt: string;
}

// ===== REPORTING TYPES =====

export interface ReportConfig {
  type: 'summary' | 'detailed' | 'quarterly' | 'daily' | 'custom';
  format: 'pdf' | 'csv' | 'json' | 'html';
  quarter?: string;
  startDate?: string;
  endDate?: string;
  servers?: string[];
  groups?: string[];
  environments?: string[];
  includeDetails: boolean;
  includeCharts: boolean;
  includeAuditTrail: boolean;
  recipients?: string[];
  schedule?: {
    frequency: 'once' | 'daily' | 'weekly' | 'monthly' | 'quarterly';
    time: string;
    daysOfWeek?: number[];
    dayOfMonth?: number;
  };
}

export interface Report {
  id: string;
  name: string;
  type: string;
  format: string;
  config: ReportConfig;
  status: 'generating' | 'completed' | 'failed';
  progress: number;
  downloadUrl?: string;
  fileSize?: number;
  generatedBy: string;
  generatedAt: string;
  expiresAt?: string;
  error?: string;
}

// ===== SYSTEM TYPES =====

export interface SystemHealth {
  overall: 'healthy' | 'warning' | 'critical';
  components: {
    database: HealthStatus;
    ssh: HealthStatus;
    email: HealthStatus;
    logging: HealthStatus;
    storage: HealthStatus;
    memory: HealthStatus;
    cpu: HealthStatus;
  };
  metrics: {
    uptime: number;
    totalServers: number;
    activeConnections: number;
    queueSize: number;
    averageResponseTime: number;
    errorRate: number;
  };
  timestamp: string;
}

export interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical';
  message: string;
  details?: any;
  lastCheck: string;
}

export interface SystemStats {
  patching: {
    totalJobs: number;
    completedJobs: number;
    failedJobs: number;
    successRate: number;
    averageDuration: number;
    totalServersPatched: number;
    totalPatchesApplied: number;
  };
  servers: {
    total: number;
    active: number;
    inactive: number;
    byOS: Record<string, number>;
    byGroup: Record<string, number>;
    byEnvironment: Record<string, number>;
  };
  approvals: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
    expired: number;
  };
  system: {
    uptime: number;
    version: string;
    lastRestart: string;
    activeUsers: number;
    totalRequests: number;
    averageResponseTime: number;
  };
  timestamp: string;
}

// ===== AUDIT TYPES =====

export interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  resource: string;
  resourceId?: string;
  userId: string;
  username: string;
  userRole: string;
  ipAddress: string;
  userAgent: string;
  details: any;
  result: 'success' | 'failure';
  errorMessage?: string;
  sessionId?: string;
  requestId?: string;
}

// ===== WEBSOCKET TYPES =====

export interface WebSocketMessage {
  type: 'job_update' | 'server_status' | 'system_alert' | 'notification';
  data: any;
  timestamp: string;
}

export interface JobUpdateMessage {
  jobId: string;
  status: string;
  progress: number;
  message?: string;
  serverResults?: PatchingServerResult[];
}

export interface ServerStatusMessage {
  serverId: string;
  status: string;
  connectivity: 'connected' | 'disconnected';
  lastSeen: string;
}

export interface SystemAlertMessage {
  level: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  category: string;
  timestamp: string;
}

// ===== NOTIFICATION TYPES =====

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  actionText?: string;
  metadata?: any;
  timestamp: string;
  expiresAt?: string;
}

// ===== FORM TYPES =====

export interface ServerFormData {
  serverName: string;
  hostGroup: string;
  operatingSystem: string;
  environment: string;
  serverTimezone: string;
  location: string;
  primaryOwner: string;
  secondaryOwner?: string;
  primaryLinuxUser: string;
  secondaryLinuxUser?: string;
  patcherEmail: string;
  sshPort: number;
  backupRequired: boolean;
  autoApprove: boolean;
  criticalServices: string[];
  notificationEmail?: string;
}

export interface PatchingJobFormData {
  name: string;
  description?: string;
  servers: string[];
  quarter?: string;
  dryRun: boolean;
  force: boolean;
  skipPrecheck: boolean;
  skipPostcheck: boolean;
  scheduledAt?: string;
}

export interface ApprovalFormData {
  serverId: string;
  quarter: string;
  businessJustification: string;
  riskAssessment: string;
  rollbackPlan: string;
  emergencyContact: string;
  maintenanceWindow: string;
  dependencies: string[];
  testingRequired: boolean;
  backupRequired: boolean;
  changeRequestId?: string;
}

// ===== FILTER TYPES =====

export interface ServerFilters {
  search?: string;
  groups?: string[];
  environments?: string[];
  operatingSystems?: string[];
  statuses?: string[];
  owners?: string[];
  lastPatchedBefore?: string;
  lastPatchedAfter?: string;
  connectivityStatus?: string[];
}

export interface JobFilters {
  search?: string;
  statuses?: string[];
  types?: string[];
  quarters?: string[];
  operators?: string[];
  startDate?: string;
  endDate?: string;
}

export interface ApprovalFilters {
  search?: string;
  statuses?: string[];
  quarters?: string[];
  requesters?: string[];
  approvers?: string[];
  approvalTypes?: string[];
  requestDateFrom?: string;
  requestDateTo?: string;
}

// ===== DASHBOARD TYPES =====

export interface DashboardStats {
  serversTotal: number;
  serversActive: number;
  serversInactive: number;
  jobsRunning: number;
  jobsCompleted: number;
  jobsFailed: number;
  approvalsNeeded: number;
  systemHealth: 'healthy' | 'warning' | 'critical';
  lastUpdate: string;
}

export interface DashboardChart {
  id: string;
  title: string;
  type: 'line' | 'bar' | 'pie' | 'area';
  data: any[];
  config: any;
}

// ===== CONFIGURATION TYPES =====

export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    realTimeUpdates: boolean;
    autoRefresh: boolean;
    darkMode: boolean;
    notifications: boolean;
    advancedFilters: boolean;
    bulkOperations: boolean;
    exportFeatures: boolean;
    auditLogs: boolean;
  };
  limits: {
    maxFileSize: number;
    maxServersPerJob: number;
    maxConcurrentJobs: number;
    requestTimeout: number;
    refreshInterval: number;
  };
  ui: {
    theme: 'light' | 'dark' | 'auto';
    pageSize: number;
    autoSave: boolean;
    confirmDestructive: boolean;
  };
}