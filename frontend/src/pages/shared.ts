import type { ConfigResponseData, HealthResponseData } from "../types/api";
import type { AnalyticsDashboardData, AnalyticsHealthData, AnalyticsSummaryData } from "../types/api";
import type { ApiClient } from "../api/client";

export interface SnapshotEntry {
  timestamp: string;
  data: unknown;
}

export type SnapshotStore = Record<string, SnapshotEntry | undefined>;

export interface WorkspaceProps {
  client: ApiClient;
  snapshots: SnapshotStore;
  onSnapshot: (key: string, data: unknown) => void;
  health: HealthResponseData | null;
  config: ConfigResponseData | null;
  analyticsSummary?: AnalyticsSummaryData | null;
  analyticsDashboard?: AnalyticsDashboardData | null;
  analyticsHealth?: AnalyticsHealthData | null;
}

export function getSnapshot<T = unknown>(snapshots: SnapshotStore, key: string): T | null {
  const entry = snapshots[key];
  return entry ? (entry.data as T) : null;
}

export function getSnapshotChain<T = unknown>(snapshots: SnapshotStore, keys: string[]): T | null {
  for (const key of keys) {
    const entry = snapshots[key];
    if (entry && entry.data != null) {
      return entry.data as T;
    }
  }
  return null;
}

export function parseCsvList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinCsvList(value: string[]): string {
  return value.join(", ");
}
