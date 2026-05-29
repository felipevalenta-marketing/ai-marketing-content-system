import { API_ENDPOINTS } from "./endpoints";
import type {
  ApiResponse,
  AssetRequest,
  CampaignRequest,
  ConfigResponseData,
  GenerateRequest,
  HealthResponseData,
  MarkdownReportRequest,
  StorageRecord,
  WorkflowRequest,
} from "../types/api";

export interface ApiClient {
  baseUrl: string;
  request<T>(path: string, init?: RequestInit & { timeoutMs?: number }): Promise<ApiResponse<T>>;
  getHealth(): Promise<ApiResponse<HealthResponseData>>;
  getConfig(): Promise<ApiResponse<ConfigResponseData>>;
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
