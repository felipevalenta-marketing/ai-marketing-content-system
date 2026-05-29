export interface StorageListResponse {
  records?: Array<Record<string, unknown>>;
  count?: number;
  record_type?: string | null;
  [key: string]: unknown;
}
