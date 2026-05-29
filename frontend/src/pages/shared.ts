import type { ConfigResponseData, HealthResponseData } from "../types/api";
import type { AnalyticsDashboardData, AnalyticsHealthData, AnalyticsSummaryData, BrandDefaults, BrandProfile, BrandRegistryEntry } from "../types/api";
import type { OrganizationProfile, OrganizationRegistryEntry, TeamProfile, MembershipProfile } from "../types/api";
import type { OrganizationContext } from "../types/api";
import type { ObservabilityConfigurationData, ObservabilityDomainsData, ObservabilityErrorsData, ObservabilityHealthData, ObservabilityMetricsData, ObservabilityStatusData, RuntimeDiagnosticsData, StorageObservabilityData, WorkflowObservabilityData, TokenObservabilityData, CostObservabilityData } from "../types/api";
import type { SecurityConfigurationData, SecurityDependencyData, SecurityFindingsData, SecurityHealthData, SecurityStatusData, ReleaseChecklistData, ReleaseHealthData, ReleaseReadinessData, ReleaseReportData, ReleaseScoreData, ReleaseStatusData } from "../types/api";
import type { ReleaseCertificationData, ReleaseGovernanceData, ReleaseExecutiveSummaryData, ReleaseMaturityData, ReleaseArtifactIndexData } from "../types/api";
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
  role?: string;
  permissions?: string[];
  activeBrand?: string;
  activeOrganizationId?: string;
  activeTeamId?: string;
  brandProfile?: BrandProfile | null;
  brandValidation?: Record<string, unknown> | null;
  brandDefaults?: BrandDefaults | null;
  brands?: BrandRegistryEntry[];
  organizations?: OrganizationRegistryEntry[];
  organizationProfile?: OrganizationProfile | null;
  organizationContext?: OrganizationContext | null;
  organizationTeams?: TeamProfile[];
  organizationMembers?: MembershipProfile[];
  analyticsSummary?: AnalyticsSummaryData | null;
  analyticsDashboard?: AnalyticsDashboardData | null;
  analyticsHealth?: AnalyticsHealthData | null;
  observabilityHealth?: ObservabilityHealthData | null;
  observabilityStatus?: ObservabilityStatusData | null;
  observabilityDomains?: ObservabilityDomainsData | null;
  observabilityTokens?: TokenObservabilityData | null;
  observabilityCosts?: CostObservabilityData | null;
  observabilityConfiguration?: ObservabilityConfigurationData | null;
  observabilityMetrics?: ObservabilityMetricsData | null;
  runtimeDiagnostics?: RuntimeDiagnosticsData | null;
  recentErrors?: ObservabilityErrorsData | null;
  workflowObservability?: WorkflowObservabilityData | null;
  storageObservability?: StorageObservabilityData | null;
  securityStatus?: SecurityStatusData | null;
  securityHealth?: SecurityHealthData | null;
  securityFindings?: SecurityFindingsData | null;
  securityDependencies?: SecurityDependencyData | null;
  securityConfiguration?: SecurityConfigurationData | null;
  releaseStatus?: ReleaseStatusData | null;
  releaseCertification?: ReleaseCertificationData | null;
  releaseMaturity?: ReleaseMaturityData | null;
  releaseGovernance?: ReleaseGovernanceData | null;
  releaseReadiness?: ReleaseReadinessData | null;
  releaseHealth?: ReleaseHealthData | null;
  releaseChecklist?: ReleaseChecklistData | null;
  releaseReport?: ReleaseReportData | null;
  releaseExecutiveSummary?: ReleaseExecutiveSummaryData | null;
  releaseArtifacts?: ReleaseArtifactIndexData | null;
  releaseScore?: ReleaseScoreData | null;
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
