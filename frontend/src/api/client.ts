import { API_ENDPOINTS } from "./endpoints";
import type {
  AnalyticsDashboardData,
  AnalyticsHealthData,
  AnalyticsRequest,
  AnalyticsResult,
  AnalyticsSummaryData,
  ApiResponse,
  AssetRequest,
  CampaignRequest,
  BrandProfile,
  BrandHealth,
  BrandRegistry,
  ConfigurationHealthData,
  ConfigurationSummaryData,
  ConfigResponseData,
  AuthResult,
  LoginRequest,
  GenerateRequest,
  HealthResponseData,
  MarkdownReportRequest,
  StorageRecord,
  RegisterRequest,
  AccessSummary,
  PermissionInfo,
  PermissionDomainInfo,
  RoleInfo,
  UserProfile,
  UserListResponse,
  UserRoleUpdateRequest,
  UserProfileUpdateRequest,
  WorkflowRequest,
} from "../types/api";

export interface ApiClient {
  baseUrl: string;
  request<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<ApiResponse<T>>;
  getHealth(): Promise<ApiResponse<HealthResponseData>>;
  getConfig(): Promise<ApiResponse<ConfigResponseData>>;
  getConfiguration(): Promise<ApiResponse<ConfigurationSummaryData>>;
  getPlatformConfig(): Promise<ApiResponse<ConfigResponseData>>;
  getFeatureFlags(): Promise<ApiResponse<{ features?: Record<string, boolean> }>>;
  getModules(): Promise<ApiResponse<{ modules?: Array<Record<string, unknown>> }>>;
  getLimits(): Promise<ApiResponse<{ limits?: Record<string, number> }>>;
  getEnvironment(): Promise<ApiResponse<{ environment?: string; debug?: boolean; show_stack_traces?: boolean }>>;
  getConfigurationHealth(): Promise<ApiResponse<ConfigurationHealthData>>;
  updateFeatureFlag(flag: string, enabled: boolean): Promise<ApiResponse<Record<string, unknown>>>;
  getBrands(): Promise<ApiResponse<BrandRegistry>>;
  getBrandProfile(brandId: string): Promise<ApiResponse<BrandProfile>>;
  validateBrand(brandId: string): Promise<ApiResponse<Record<string, unknown>>>;
  getBrandDefaults(brandId: string): Promise<ApiResponse<Record<string, unknown>>>;
  getBrandHealth(brandId: string): Promise<ApiResponse<BrandHealth>>;
  getRoles(): Promise<ApiResponse<{ roles?: RoleInfo[]; permissions?: PermissionInfo[] }>>;
  getPermissions(): Promise<ApiResponse<{ permissions?: PermissionInfo[]; grouped?: Record<string, PermissionInfo[]>; domains?: PermissionDomainInfo[] }>>;
  getMyAccess(): Promise<ApiResponse<AccessSummary>>;
  register(payload: RegisterRequest): Promise<ApiResponse<AuthResult>>;
  login(payload: LoginRequest): Promise<ApiResponse<AuthResult>>;
  logout(): Promise<ApiResponse<AuthResult>>;
  getCurrentUser(): Promise<ApiResponse<AuthResult>>;
  updateProfile(payload: UserProfileUpdateRequest): Promise<ApiResponse<AuthResult>>;
  listUsers(): Promise<ApiResponse<UserListResponse>>;
  updateUserRole(userId: string, role: string): Promise<ApiResponse<Record<string, unknown>>>;
  getAnalyticsSummary(): Promise<ApiResponse<AnalyticsSummaryData>>;
  getAnalyticsDashboard(): Promise<ApiResponse<AnalyticsDashboardData>>;
  queryAnalytics(payload: AnalyticsRequest): Promise<ApiResponse<AnalyticsResult>>;
  getAnalyticsHealth(): Promise<ApiResponse<AnalyticsHealthData>>;
  generateContent(payload: GenerateRequest): Promise<ApiResponse<unknown>>;
  runWorkflow(payload: WorkflowRequest): Promise<ApiResponse<unknown>>;
  runCampaign(payload: CampaignRequest): Promise<ApiResponse<unknown>>;
  runAssets(payload: AssetRequest): Promise<ApiResponse<unknown>>;
  generateMarkdownReport(payload: MarkdownReportRequest): Promise<ApiResponse<unknown>>;
  getLatestReports(): Promise<ApiResponse<unknown>>;
  listStorageRecords(recordType?: string): Promise<ApiResponse<{ records?: StorageRecord[]; count?: number; record_type?: string | null }>>;
  getStorageRecord(recordType: string, recordId: string): Promise<ApiResponse<StorageRecord>>;
}

const DEFAULT_TIMEOUT_MS = 30000;
const AUTH_TOKEN_KEY = "amcs:auth-token";

function readAuthToken(): string {
  if (typeof window === "undefined") {
    return "";
  }
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

function buildUrl(baseUrl: string, path: string): string {
  const normalizedBase = baseUrl.replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

async function safeJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { success: false, data: null, warnings: [], errors: [text], metadata: {} };
  }
}

function normalizeError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed.";
}

function buildFailure(message: string): ApiResponse<never> {
  return {
    success: false,
    data: null,
    warnings: [],
    errors: [message],
    metadata: {},
  };
}

export function createApiClient(baseUrl = "http://127.0.0.1:8000"): ApiClient {
  const request = async <T>(path: string, init: RequestInit & { timeoutMs?: number } = {}): Promise<ApiResponse<T>> => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), init.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    try {
      const response = await fetch(buildUrl(baseUrl, path), {
        method: init.method ?? "GET",
        headers: {
          Accept: "application/json",
          "Content-Type": init.body ? "application/json" : "application/json",
          ...(readAuthToken() ? { Authorization: `Bearer ${readAuthToken()}` } : {}),
          ...(init.headers ?? {}),
        },
        body: init.body as BodyInit | null | undefined,
        signal: controller.signal,
      });
      const parsed = (await safeJson(response)) as ApiResponse<T> | Record<string, unknown> | null;
      if (parsed && typeof parsed === "object" && "success" in parsed) {
        return parsed as ApiResponse<T>;
      }
      if (!response.ok) {
        return buildFailure(`Request failed with status ${response.status}.`);
      }
      return {
        success: true,
        data: parsed as T,
        warnings: [],
        errors: [],
        metadata: { status: response.status },
      };
    } catch (error) {
      return buildFailure(normalizeError(error));
    } finally {
      window.clearTimeout(timeout);
    }
  };

  return {
    baseUrl,
    request,
    getHealth: () => request<HealthResponseData>(API_ENDPOINTS.health),
    getConfig: () => request<ConfigResponseData>(API_ENDPOINTS.config),
    getConfiguration: () => request<ConfigurationSummaryData>(API_ENDPOINTS.configuration),
    getPlatformConfig: () => request<ConfigResponseData>(API_ENDPOINTS.configurationPlatform),
    getFeatureFlags: () => request<{ features?: Record<string, boolean> }>(API_ENDPOINTS.configurationFeatures),
    getModules: () => request<{ modules?: Array<Record<string, unknown>> }>(API_ENDPOINTS.configurationModules),
    getLimits: () => request<{ limits?: Record<string, number> }>(API_ENDPOINTS.configurationLimits),
    getEnvironment: () => request<{ environment?: string; debug?: boolean; show_stack_traces?: boolean }>(API_ENDPOINTS.configurationEnvironment),
    getConfigurationHealth: () => request<ConfigurationHealthData>(API_ENDPOINTS.configurationHealth),
    updateFeatureFlag: (flag: string, enabled: boolean) =>
      request<Record<string, unknown>>(API_ENDPOINTS.configurationFeatureFlag(flag), {
        method: "PATCH",
        body: JSON.stringify({ enabled }),
      }),
    getBrands: () => request<BrandRegistry>(API_ENDPOINTS.brands),
    getBrandProfile: (brandId: string) => request<BrandProfile>(`${API_ENDPOINTS.brands}/${encodeURIComponent(brandId)}`),
    validateBrand: (brandId: string) => request<Record<string, unknown>>(`${API_ENDPOINTS.brands}/${encodeURIComponent(brandId)}/validate`),
    getBrandDefaults: (brandId: string) => request<Record<string, unknown>>(`${API_ENDPOINTS.brands}/${encodeURIComponent(brandId)}/defaults`),
    getBrandHealth: (brandId: string) => request<BrandHealth>(`${API_ENDPOINTS.brands}/${encodeURIComponent(brandId)}/health`),
    getRoles: () => request<{ roles?: RoleInfo[]; permissions?: PermissionInfo[] }>(API_ENDPOINTS.rbacRoles),
    getPermissions: () => request<{ permissions?: PermissionInfo[]; grouped?: Record<string, PermissionInfo[]>; domains?: PermissionDomainInfo[] }>(API_ENDPOINTS.rbacPermissions),
    getMyAccess: () => request<AccessSummary>(API_ENDPOINTS.rbacMe),
    register: (payload: RegisterRequest) =>
      request<AuthResult>(API_ENDPOINTS.authRegister, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    login: (payload: LoginRequest) =>
      request<AuthResult>(API_ENDPOINTS.authLogin, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    logout: () =>
      request<AuthResult>(API_ENDPOINTS.authLogout, {
        method: "POST",
      }),
    getCurrentUser: () => request<AuthResult>(API_ENDPOINTS.authMe),
    updateProfile: (payload: UserProfileUpdateRequest) =>
      request<AuthResult>(API_ENDPOINTS.usersProfile, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    listUsers: () => request<UserListResponse>(API_ENDPOINTS.usersList),
    updateUserRole: (userId: string, role: string) =>
      request<Record<string, unknown>>(API_ENDPOINTS.userRole(userId), {
        method: "PATCH",
        body: JSON.stringify({ role } satisfies UserRoleUpdateRequest),
      }),
    getAnalyticsSummary: () => request<AnalyticsSummaryData>(API_ENDPOINTS.analyticsSummary),
    getAnalyticsDashboard: () => request<AnalyticsDashboardData>(API_ENDPOINTS.analyticsDashboard),
    queryAnalytics: (payload: AnalyticsRequest) =>
      request<AnalyticsResult>(API_ENDPOINTS.analyticsQuery, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    getAnalyticsHealth: () => request<AnalyticsHealthData>(API_ENDPOINTS.analyticsHealth),
    generateContent: (payload: GenerateRequest) =>
      request(API_ENDPOINTS.generate, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    runWorkflow: (payload: WorkflowRequest) =>
      request(API_ENDPOINTS.workflow, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    runCampaign: (payload: CampaignRequest) =>
      request(API_ENDPOINTS.campaign, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    runAssets: (payload: AssetRequest) =>
      request(API_ENDPOINTS.assets, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    generateMarkdownReport: (payload: MarkdownReportRequest) =>
      request(API_ENDPOINTS.markdownReport, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    getLatestReports: () => request(API_ENDPOINTS.latestReports),
    listStorageRecords: (recordType?: string) => {
      const suffix = recordType ? `?record_type=${encodeURIComponent(recordType)}` : "";
      return request<{ records?: StorageRecord[]; count?: number; record_type?: string | null }>(`${API_ENDPOINTS.storageRecords}${suffix}`);
    },
    getStorageRecord: (recordType: string, recordId: string) =>
      request<StorageRecord>(`${API_ENDPOINTS.storageRecords}/${encodeURIComponent(recordType)}/${encodeURIComponent(recordId)}`),
  };
}
