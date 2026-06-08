import { useEffect, useState } from "react";
import { AppShell } from "./components/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { ContentStudio } from "./pages/ContentStudio";
import { WorkflowCenter } from "./pages/WorkflowCenter";
import { CampaignStudio } from "./pages/CampaignStudio";
import { AssetStudio } from "./pages/AssetStudio";
import { ReportsCenter } from "./pages/ReportsCenter";
import { StorageExplorer } from "./pages/StorageExplorer";
import { AnalyticsCenter } from "./pages/AnalyticsCenter";
import { GovernanceCenter } from "./pages/GovernanceCenter";
import { SystemConfig } from "./pages/SystemConfig";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Profile } from "./pages/Profile";
import type { SnapshotStore } from "./pages/shared";
import { useApi } from "./hooks/useApi";
import { useAuth } from "./hooks/useAuth";
import { useConfig } from "./hooks/useConfig";
import { useHealth } from "./hooks/useHealth";
import { useLocalState } from "./hooks/useLocalState";
import { Button } from "./components/Button";
import { Card } from "./components/Card";
import { SectionHeader } from "./components/SectionHeader";
import { AuthGuard } from "./components/AuthGuard";
import { PermissionGate } from "./components/PermissionGate";
import { EmptyState } from "./components/EmptyState";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Badge } from "./components/Badge";
import { isUnauthorizedResponse, createApiClient } from "./api/client";
import {
  DEMO_ANALYTICS_DASHBOARD,
  DEMO_ANALYTICS_HEALTH,
  DEMO_ANALYTICS_SUMMARY,
  DEMO_BRAND_DEFAULTS,
  DEMO_BRAND_PROFILE,
  DEMO_BRANDS,
  DEMO_CONFIG,
  DEMO_HEALTH,
  DEMO_ORGANIZATION_CONTEXT,
  DEMO_ORGANIZATION_ID,
  DEMO_ORGANIZATION_PROFILE,
  DEMO_RELEASE_CERTIFICATION,
  DEMO_RELEASE_CHECKLIST,
  DEMO_RELEASE_GOVERNANCE,
  DEMO_RELEASE_HEALTH,
  DEMO_RELEASE_MATURITY,
  DEMO_RELEASE_READINESS,
  DEMO_RELEASE_REPORT,
  DEMO_RELEASE_SCORE,
  DEMO_RELEASE_STATUS,
  DEMO_SNAPSHOTS,
  DEMO_TEAMS,
} from "./utils/demo";
import type {
  AnalyticsDashboardData,
  AnalyticsHealthData,
  AnalyticsSummaryData,
  BrandDefaults,
  BrandProfile,
  BrandRegistryEntry,
  OrganizationContext,
  MembershipProfile,
  OrganizationProfile,
  OrganizationRegistryEntry,
  ObservabilityErrorsData,
  ObservabilityHealthData,
  ObservabilityStatusData,
  ObservabilityDomainsData,
  ObservabilityConfigurationData,
  ObservabilityMetricsData,
  RuntimeDiagnosticsData,
  TokenObservabilityData,
  CostObservabilityData,
  TeamProfile,
  StorageObservabilityData,
  WorkflowObservabilityData,
  SecurityConfigurationData,
  SecurityDependencyData,
  SecurityFindingsData,
  SecurityHealthData,
  SecurityStatusData,
  ReleaseChecklistData,
  ReleaseCertificationData,
  ReleaseHealthData,
  ReleaseGovernanceData,
  ReleaseExecutiveSummaryData,
  ReleaseMaturityData,
  ReleaseReadinessData,
  ReleaseReportData,
  ReleaseScoreData,
  ReleaseStatusData,
} from "./types/api";
import { IS_DEMO_MODE } from "./utils/demo";

type PageKey =
  | "dashboard"
  | "content"
  | "workflow"
  | "campaign"
  | "assets"
  | "reports"
  | "storage"
  | "analytics"
  | "governance"
  | "config"
  | "login"
  | "register"
  | "profile";

const SNAPSHOT_DEFAULT: SnapshotStore = {};

export default function App() {
  const { apiBaseUrl, setApiBaseUrl, client } = useApi();
  const auth = useAuth(client);
  const { data: health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(apiBaseUrl, !IS_DEMO_MODE);
  const { data: config, loading: configLoading, error: configError, refresh: refreshConfig } = useConfig(apiBaseUrl, auth.isAuthenticated && !IS_DEMO_MODE);
  const [activePage, setActivePage] = useLocalState<PageKey>("amcs:active-page", IS_DEMO_MODE ? "dashboard" : "dashboard");
  const [activeBrand, setActiveBrand] = useLocalState<string>("amcs:active-brand", "wenzel_partner");
  const [activeOrganizationId, setActiveOrganizationId] = useLocalState<string>("amcs:active-organization", IS_DEMO_MODE ? DEMO_ORGANIZATION_ID : "");
  const [activeTeamId, setActiveTeamId] = useLocalState<string>("amcs:active-team", IS_DEMO_MODE ? "demo_team" : "");
  const [snapshots, setSnapshots] = useLocalState<SnapshotStore>("amcs:snapshots", IS_DEMO_MODE ? (DEMO_SNAPSHOTS as unknown as SnapshotStore) : SNAPSHOT_DEFAULT);
  const [brands, setBrands] = useState<BrandRegistryEntry[]>(() => (IS_DEMO_MODE ? (DEMO_BRANDS as BrandRegistryEntry[]) : []));
  const [organizations, setOrganizations] = useState<OrganizationRegistryEntry[]>(() => (IS_DEMO_MODE ? ([DEMO_ORGANIZATION_PROFILE] as OrganizationRegistryEntry[]) : []));
  const [organizationProfile, setOrganizationProfile] = useState<OrganizationProfile | null>(() => (IS_DEMO_MODE ? (DEMO_ORGANIZATION_PROFILE as unknown as OrganizationProfile) : null));
  const [organizationContext, setOrganizationContext] = useState<OrganizationContext | null>(() => (IS_DEMO_MODE ? (DEMO_ORGANIZATION_CONTEXT as unknown as OrganizationContext) : null));
  const [organizationTeams, setOrganizationTeams] = useState<TeamProfile[]>(() => (IS_DEMO_MODE ? (DEMO_TEAMS as TeamProfile[]) : []));
  const [organizationMembers, setOrganizationMembers] = useState<MembershipProfile[]>(() => (IS_DEMO_MODE ? ([{ membership_id: "demo-membership", organization_id: DEMO_ORGANIZATION_ID, team_id: "demo_team", user_id: auth.currentUser?.user_id ?? "demo-admin", role: "owner", status: "active", metadata: { demo_mode: true } }] as MembershipProfile[]) : []));
  const [brandProfile, setBrandProfile] = useState<BrandProfile | null>(() => (IS_DEMO_MODE ? (DEMO_BRAND_PROFILE as BrandProfile) : null));
  const [brandValidation, setBrandValidation] = useState<Record<string, unknown> | null>(() => (IS_DEMO_MODE ? ({ valid: true, warnings: [], errors: [] } as Record<string, unknown>) : null));
  const [brandDefaults, setBrandDefaults] = useState<BrandDefaults | null>(() => (IS_DEMO_MODE ? (DEMO_BRAND_DEFAULTS as BrandDefaults) : null));
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummaryData | null>(() => (IS_DEMO_MODE ? (DEMO_ANALYTICS_SUMMARY as AnalyticsSummaryData) : null));
  const [analyticsDashboard, setAnalyticsDashboard] = useState<AnalyticsDashboardData | null>(() => (IS_DEMO_MODE ? (DEMO_ANALYTICS_DASHBOARD as AnalyticsDashboardData) : null));
  const [analyticsHealth, setAnalyticsHealth] = useState<AnalyticsHealthData | null>(() => (IS_DEMO_MODE ? (DEMO_ANALYTICS_HEALTH as AnalyticsHealthData) : null));
  const [observabilityHealth, setObservabilityHealth] = useState<ObservabilityHealthData | null>(null);
  const [observabilityStatus, setObservabilityStatus] = useState<ObservabilityStatusData | null>(null);
  const [observabilityDomains, setObservabilityDomains] = useState<ObservabilityDomainsData | null>(null);
  const [observabilityTokens, setObservabilityTokens] = useState<TokenObservabilityData | null>(null);
  const [observabilityCosts, setObservabilityCosts] = useState<CostObservabilityData | null>(null);
  const [observabilityConfiguration, setObservabilityConfiguration] = useState<ObservabilityConfigurationData | null>(null);
  const [observabilityMetrics, setObservabilityMetrics] = useState<ObservabilityMetricsData | null>(null);
  const [runtimeDiagnostics, setRuntimeDiagnostics] = useState<RuntimeDiagnosticsData | null>(null);
  const [recentErrors, setRecentErrors] = useState<ObservabilityErrorsData | null>(null);
  const [workflowObservability, setWorkflowObservability] = useState<WorkflowObservabilityData | null>(null);
  const [storageObservability, setStorageObservability] = useState<StorageObservabilityData | null>(null);
  const [securityStatus, setSecurityStatus] = useState<SecurityStatusData | null>(null);
  const [securityHealth, setSecurityHealth] = useState<SecurityHealthData | null>(null);
  const [securityFindings, setSecurityFindings] = useState<SecurityFindingsData | null>(null);
  const [securityDependencies, setSecurityDependencies] = useState<SecurityDependencyData | null>(null);
  const [securityConfiguration, setSecurityConfiguration] = useState<SecurityConfigurationData | null>(null);
  const [releaseStatus, setReleaseStatus] = useState<ReleaseStatusData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_STATUS as ReleaseStatusData) : null));
  const [releaseCertification, setReleaseCertification] = useState<ReleaseCertificationData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_CERTIFICATION as ReleaseCertificationData) : null));
  const [releaseMaturity, setReleaseMaturity] = useState<ReleaseMaturityData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_MATURITY as ReleaseMaturityData) : null));
  const [releaseGovernance, setReleaseGovernance] = useState<ReleaseGovernanceData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_GOVERNANCE as ReleaseGovernanceData) : null));
  const [releaseExecutiveSummary, setReleaseExecutiveSummary] = useState<ReleaseExecutiveSummaryData | null>(null);
  const [releaseReadiness, setReleaseReadiness] = useState<ReleaseReadinessData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_READINESS as ReleaseReadinessData) : null));
  const [releaseHealth, setReleaseHealth] = useState<ReleaseHealthData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_HEALTH as ReleaseHealthData) : null));
  const [releaseChecklist, setReleaseChecklist] = useState<ReleaseChecklistData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_CHECKLIST as ReleaseChecklistData) : null));
  const [releaseReport, setReleaseReport] = useState<ReleaseReportData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_REPORT as ReleaseReportData) : null));
  const [releaseScore, setReleaseScore] = useState<ReleaseScoreData | null>(() => (IS_DEMO_MODE ? (DEMO_RELEASE_SCORE as ReleaseScoreData) : null));
  const [authWarning, setAuthWarning] = useState<string | null>(null);
  const effectivePage: PageKey = IS_DEMO_MODE && (activePage === "login" || activePage === "register") ? "dashboard" : activePage;
  const isPublicPage = !IS_DEMO_MODE && (effectivePage === "login" || effectivePage === "register");
  const shouldLoadPrivateData = !IS_DEMO_MODE && auth.isAuthenticated && !auth.loading && !isPublicPage && !authWarning;
  const permissions = auth.permissions;
  const role = auth.role;
  const isDemoMode = IS_DEMO_MODE;
  const resolvedHealth = IS_DEMO_MODE ? DEMO_HEALTH : health;
  const resolvedHealthLoading = IS_DEMO_MODE ? false : healthLoading;
  const resolvedHealthError = IS_DEMO_MODE ? "" : healthError;
  const resolvedConfig = IS_DEMO_MODE ? DEMO_CONFIG : config;
  const resolvedConfigLoading = IS_DEMO_MODE ? false : configLoading;
  const resolvedConfigError = IS_DEMO_MODE ? "" : configError;

  useEffect(() => {
    if (!IS_DEMO_MODE) {
      return;
    }
    setActiveBrand("wenzel_partner");
    setActiveOrganizationId(DEMO_ORGANIZATION_ID);
    setActiveTeamId("demo_team");
    if (!auth.isAuthenticated || isPublicPage) {
      setAuthWarning(null);
    }
  }, [activePage, auth.isAuthenticated, isPublicPage, setActiveBrand, setActiveOrganizationId, setActiveTeamId]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      setAuthWarning(null);
      return;
    }
    if (!shouldLoadPrivateData) {
      setAnalyticsSummary(null);
      setAnalyticsDashboard(null);
      setAnalyticsHealth(null);
      return;
    }
    let active = true;
    const analyticsClient = createApiClient(apiBaseUrl);
    Promise.all([
      analyticsClient.getAnalyticsSummary(),
      analyticsClient.getAnalyticsDashboard(),
      analyticsClient.getAnalyticsHealth(),
    ]).then(([summaryResponse, dashboardResponse, healthResponse]) => {
      if (!active) {
        return;
      }
      if (summaryResponse.success && summaryResponse.data) {
        setAnalyticsSummary(summaryResponse.data);
      }
      if (dashboardResponse.success && dashboardResponse.data) {
        setAnalyticsDashboard(dashboardResponse.data);
      }
      if (healthResponse.success && healthResponse.data) {
        setAnalyticsHealth(healthResponse.data);
      }
    });
    return () => {
      active = false;
    };
  }, [apiBaseUrl, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      setObservabilityHealth(null);
      setObservabilityStatus(null);
      setObservabilityDomains(null);
      setObservabilityTokens(null);
      setObservabilityCosts(null);
      setObservabilityConfiguration(null);
      setObservabilityMetrics(null);
      setRuntimeDiagnostics(null);
      setRecentErrors(null);
      setWorkflowObservability(null);
      setStorageObservability(null);
      setSecurityStatus(null);
      setSecurityHealth(null);
      setSecurityFindings(null);
      setSecurityDependencies(null);
      setSecurityConfiguration(null);
      setReleaseStatus(null);
      setReleaseCertification(null);
      setReleaseMaturity(null);
      setReleaseGovernance(null);
      setReleaseExecutiveSummary(null);
      setReleaseReadiness(null);
      setReleaseHealth(null);
      setReleaseChecklist(null);
      setReleaseReport(null);
      setReleaseScore(null);
      return;
    }
    let active = true;
    Promise.all([
      client.getObservabilityHealth(),
      client.getObservabilityStatus(),
      client.getObservabilityDomains(),
      client.getObservabilityTokens(),
      client.getObservabilityCosts(),
      client.getObservabilityConfiguration(),
      client.getObservabilityMetrics(),
      client.getRuntimeDiagnostics(),
      client.getRecentErrors(),
      client.getWorkflowObservability(),
      client.getStorageObservability(),
      client.getSecurityStatus(),
      client.getSecurityHealth(),
      client.getSecurityFindings(),
      client.getSecurityDependencies(),
      client.getSecurityConfiguration(),
      client.getReleaseStatus(),
      client.getReleaseCertification(),
      client.getReleaseMaturity(),
      client.getReleaseGovernance(),
      client.getReleaseExecutiveSummary(),
      client.getReleaseReadiness(),
      client.getReleaseHealth(),
      client.getReleaseChecklist(),
      client.getReleaseScore(),
    ]).then(([healthResponse, statusResponse, domainsResponse, tokensResponse, costsResponse, configurationResponse, metricsResponse, runtimeResponse, errorsResponse, workflowResponse, storageResponse, securityStatusResponse, securityHealthResponse, securityFindingsResponse, securityDependenciesResponse, securityConfigurationResponse, releaseStatusResponse, releaseCertificationResponse, releaseMaturityResponse, releaseGovernanceResponse, releaseExecutiveSummaryResponse, releaseReadinessResponse, releaseHealthResponse, releaseChecklistResponse, releaseScoreResponse]) => {
      if (!active) {
        return;
      }
      setObservabilityHealth(healthResponse.success && healthResponse.data ? healthResponse.data : null);
      setObservabilityStatus(statusResponse.success && statusResponse.data ? statusResponse.data : null);
      setObservabilityDomains(domainsResponse.success && domainsResponse.data ? domainsResponse.data : null);
      setObservabilityTokens(tokensResponse.success && tokensResponse.data ? tokensResponse.data : null);
      setObservabilityCosts(costsResponse.success && costsResponse.data ? costsResponse.data : null);
      setObservabilityConfiguration(configurationResponse.success && configurationResponse.data ? configurationResponse.data : null);
      setObservabilityMetrics(metricsResponse.success && metricsResponse.data ? metricsResponse.data : null);
      setRuntimeDiagnostics(runtimeResponse.success && runtimeResponse.data ? runtimeResponse.data : null);
      setRecentErrors(errorsResponse.success && errorsResponse.data ? errorsResponse.data : null);
      setWorkflowObservability(workflowResponse.success && workflowResponse.data ? (workflowResponse.data as WorkflowObservabilityData) : null);
      setStorageObservability(storageResponse.success && storageResponse.data ? (storageResponse.data as StorageObservabilityData) : null);
      setSecurityStatus(securityStatusResponse.success && securityStatusResponse.data ? (securityStatusResponse.data as SecurityStatusData) : null);
      setSecurityHealth(securityHealthResponse.success && securityHealthResponse.data ? (securityHealthResponse.data as SecurityHealthData) : null);
      setSecurityFindings(securityFindingsResponse.success && securityFindingsResponse.data ? (securityFindingsResponse.data as SecurityFindingsData) : null);
      setSecurityDependencies(securityDependenciesResponse.success && securityDependenciesResponse.data ? (securityDependenciesResponse.data as SecurityDependencyData) : null);
      setSecurityConfiguration(securityConfigurationResponse.success && securityConfigurationResponse.data ? (securityConfigurationResponse.data as SecurityConfigurationData) : null);
      setReleaseStatus(releaseStatusResponse.success && releaseStatusResponse.data ? (releaseStatusResponse.data as ReleaseStatusData) : null);
      setReleaseCertification(releaseCertificationResponse.success && releaseCertificationResponse.data ? (releaseCertificationResponse.data as ReleaseCertificationData) : null);
      setReleaseMaturity(releaseMaturityResponse.success && releaseMaturityResponse.data ? (releaseMaturityResponse.data as ReleaseMaturityData) : null);
      setReleaseGovernance(releaseGovernanceResponse.success && releaseGovernanceResponse.data ? (releaseGovernanceResponse.data as ReleaseGovernanceData) : null);
      setReleaseExecutiveSummary(releaseExecutiveSummaryResponse.success && releaseExecutiveSummaryResponse.data ? (releaseExecutiveSummaryResponse.data as ReleaseExecutiveSummaryData) : null);
      setReleaseReadiness(releaseReadinessResponse.success && releaseReadinessResponse.data ? (releaseReadinessResponse.data as ReleaseReadinessData) : null);
      setReleaseHealth(releaseHealthResponse.success && releaseHealthResponse.data ? (releaseHealthResponse.data as ReleaseHealthData) : null);
      setReleaseChecklist(releaseChecklistResponse.success && releaseChecklistResponse.data ? (releaseChecklistResponse.data as ReleaseChecklistData) : null);
      setReleaseScore(releaseScoreResponse.success && releaseScoreResponse.data ? (releaseScoreResponse.data as ReleaseScoreData) : null);
    });
    return () => {
      active = false;
    };
  }, [auth.isAuthenticated, client, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      setBrands([]);
      return;
    }
    let active = true;
    client.getBrands().then((response) => {
      if (!active) {
        return;
      }
      if (isUnauthorizedResponse(response)) {
        setAuthWarning("Authentication token is required. Please log in again.");
        setBrands([]);
        return;
      }
      if (response.success && response.data?.brands) {
        setBrands(response.data.brands as BrandRegistryEntry[]);
      } else {
        setBrands([]);
      }
    });
    return () => {
      active = false;
    };
  }, [client, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      setOrganizations([]);
      setActiveOrganizationId("");
      return;
    }
    let active = true;
    client.getOrganizations().then((response) => {
      if (!active) {
        return;
      }
      if (isUnauthorizedResponse(response)) {
        setAuthWarning("Authentication token is required. Please log in again.");
        setOrganizations([]);
        setActiveOrganizationId("");
        return;
      }
      if (response.success && response.data?.organizations) {
        const entries = response.data.organizations as OrganizationRegistryEntry[];
        setOrganizations(entries);
        if (!activeOrganizationId && entries[0]?.organization_id) {
          setActiveOrganizationId(String(entries[0].organization_id));
        } else if (activeOrganizationId && !entries.some((organization) => organization.organization_id === activeOrganizationId)) {
          setActiveOrganizationId(String(entries[0]?.organization_id ?? ""));
        }
      } else {
        setOrganizations([]);
        setActiveOrganizationId("");
      }
    });
    return () => {
      active = false;
    };
  }, [client, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      setOrganizationProfile(null);
      setOrganizationContext(null);
      setOrganizationTeams([]);
      setOrganizationMembers([]);
      return;
    }
    let active = true;
    if (!activeOrganizationId) {
      setOrganizationProfile(null);
      setOrganizationContext(null);
      setOrganizationTeams([]);
      setOrganizationMembers([]);
      return () => {
        active = false;
      };
    }
    Promise.all([
      client.getOrganizationProfile(activeOrganizationId),
      client.getOrganizationContext(activeOrganizationId),
      client.getOrganizationTeams(activeOrganizationId),
      client.getMembers(activeOrganizationId),
      client.getOrganizationBrands(activeOrganizationId),
    ]).then(([profileResponse, contextResponse, teamsResponse, membersResponse]) => {
      if (!active) {
        return;
      }
      if ([profileResponse, contextResponse, teamsResponse, membersResponse].some((response) => isUnauthorizedResponse(response))) {
        setAuthWarning("Authentication token is required. Please log in again.");
        setOrganizationProfile(null);
        setOrganizationContext(null);
        setOrganizationTeams([]);
        setOrganizationMembers([]);
        return;
      }
      setOrganizationProfile(profileResponse.success && profileResponse.data ? (profileResponse.data as OrganizationProfile) : null);
      setOrganizationContext(contextResponse.success && contextResponse.data ? (contextResponse.data as OrganizationContext) : null);
      setOrganizationTeams(teamsResponse.success && teamsResponse.data?.teams ? (teamsResponse.data.teams as TeamProfile[]) : []);
      setOrganizationMembers(membersResponse.success && membersResponse.data?.memberships ? (membersResponse.data.memberships as MembershipProfile[]) : []);
    });
    return () => {
      active = false;
    };
  }, [activeOrganizationId, client, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      if (activeTeamId) {
        setActiveTeamId("");
      }
      return;
    }
    if (!activeOrganizationId || !organizationTeams.length) {
      if (!activeTeamId) {
        return;
      }
      setActiveTeamId("");
      return;
    }
    const selectedTeam = organizationTeams.find((team) => String(team.team_id ?? "") === activeTeamId);
    if (!selectedTeam) {
      setActiveTeamId(String(organizationTeams[0]?.team_id ?? ""));
    }
  }, [activeOrganizationId, activeTeamId, organizationTeams, setActiveTeamId, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!shouldLoadPrivateData) {
      setBrandProfile(null);
      setBrandValidation(null);
      setBrandDefaults(null);
      return;
    }
    let active = true;
    if (!activeBrand) {
      return () => {
        active = false;
      };
    }
    Promise.all([client.getBrandProfile(activeBrand), client.validateBrand(activeBrand), client.getBrandDefaults(activeBrand)]).then(
      ([profileResponse, validationResponse, defaultsResponse]) => {
        if (!active) {
          return;
        }
        if ([profileResponse, validationResponse, defaultsResponse].some((response) => isUnauthorizedResponse(response))) {
          setAuthWarning("Authentication token is required. Please log in again.");
          setBrandProfile(null);
          setBrandValidation(null);
          setBrandDefaults(null);
          return;
        }
        setBrandProfile(profileResponse.success && profileResponse.data ? (profileResponse.data as BrandProfile) : null);
        setBrandValidation(validationResponse.success && validationResponse.data ? (validationResponse.data as Record<string, unknown>) : null);
        const defaultsPayload = defaultsResponse.success && defaultsResponse.data ? (defaultsResponse.data as Record<string, unknown>) : null;
        setBrandDefaults((defaultsPayload?.defaults as BrandDefaults) ?? null);
      },
    );
    return () => {
      active = false;
    };
  }, [activeBrand, client, shouldLoadPrivateData]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!activeBrand && resolvedConfig?.default_brand) {
      setActiveBrand(String(resolvedConfig.default_brand));
    }
  }, [activeBrand, resolvedConfig?.default_brand, setActiveBrand]);

  useEffect(() => {
    if (!IS_DEMO_MODE && !auth.loading && !auth.isAuthenticated && activePage !== "login" && activePage !== "register") {
      setActivePage("login");
    }
  }, [activePage, auth.isAuthenticated, auth.loading, setActivePage]);

  useEffect(() => {
    if (!IS_DEMO_MODE && auth.isAuthenticated && (activePage === "login" || activePage === "register")) {
      setActivePage("dashboard");
    }
  }, [activePage, auth.isAuthenticated, setActivePage]);

  useEffect(() => {
    if (organizationProfile?.organization_id && organizationProfile.organization_id !== activeOrganizationId) {
      setActiveOrganizationId(String(organizationProfile.organization_id));
    }
    if (organizationProfile?.owner_user_id && !activeOrganizationId) {
      setActiveOrganizationId(String(organizationProfile.organization_id ?? ""));
    }
  }, [activeOrganizationId, organizationProfile?.organization_id, organizationProfile?.owner_user_id, setActiveOrganizationId]);

  useEffect(() => {
    if (!brands.length) {
      return;
    }
    const available = brands.find((brand) => brand.brand_id === activeBrand);
    if (!available) {
      const fallback = brands.find((brand) => brand.brand_id === resolvedConfig?.default_brand)?.brand_id ?? brands[0]?.brand_id;
      if (fallback && fallback !== activeBrand) {
        setActiveBrand(String(fallback));
      }
    }
  }, [activeBrand, brands, resolvedConfig?.default_brand, setActiveBrand]);

  const onSnapshot = (key: string, data: unknown) => {
    setSnapshots((current) => ({
      ...current,
      [key]: { timestamp: new Date().toISOString(), data },
    }));
  };

  const currentPage = (() => {
    const pageProps = {
      client,
      snapshots,
      onSnapshot,
      health: resolvedHealth ?? null,
      config: resolvedConfig ?? null,
      role,
      permissions,
      activeBrand,
      activeOrganizationId,
      activeTeamId,
      brandProfile,
      brandValidation,
      brandDefaults,
      brands,
      organizations,
      organizationProfile,
      organizationTeams,
      organizationMembers,
      analyticsSummary,
      analyticsDashboard,
      analyticsHealth,
      observabilityHealth,
      observabilityStatus,
      observabilityDomains,
      observabilityTokens,
      observabilityCosts,
      observabilityConfiguration,
      observabilityMetrics,
      runtimeDiagnostics,
      recentErrors,
      workflowObservability,
      storageObservability,
      securityStatus,
      securityHealth,
      securityFindings,
      securityDependencies,
      securityConfiguration,
      releaseStatus,
      releaseCertification,
      releaseMaturity,
      releaseGovernance,
      releaseExecutiveSummary,
      releaseReadiness,
      releaseHealth,
      releaseChecklist,
      releaseReport,
      releaseScore,
    };
    switch (effectivePage) {
      case "content":
        return <ContentStudio {...pageProps} />;
      case "workflow":
        return <WorkflowCenter {...pageProps} />;
      case "campaign":
        return <CampaignStudio {...pageProps} />;
      case "assets":
        return <AssetStudio {...pageProps} />;
      case "reports":
        return <ReportsCenter {...pageProps} />;
      case "storage":
        return <StorageExplorer {...pageProps} />;
      case "analytics":
        return <AnalyticsCenter {...pageProps} />;
      case "governance":
        return <GovernanceCenter {...pageProps} />;
      case "config":
        return <SystemConfig {...pageProps} />;
      case "profile":
        return <Profile client={client} auth={auth} onNavigate={setActivePage} />;
      case "login":
        return <Login client={client} auth={auth} onNavigate={setActivePage} />;
      case "register":
        return <Register client={client} auth={auth} onNavigate={setActivePage} />;
      case "dashboard":
      default:
        return <Dashboard {...pageProps} onNavigate={setActivePage} onCheckHealth={refreshHealth} />;
    }
  })();

  const pagePermission = (() => {
    switch (effectivePage) {
      case "content":
        return "generation:create";
      case "workflow":
        return "workflow:run";
      case "campaign":
        return "campaign:create";
      case "assets":
        return "asset:create";
      case "reports":
        return "report:read";
      case "storage":
        return "storage:read";
      case "analytics":
        return "analytics:read";
      case "config":
        return "system:read";
      default:
        return "";
    }
  })();

  const authOnlyPage = (() => {
    switch (effectivePage) {
      case "register":
        return <Register client={client} auth={auth} onNavigate={setActivePage} />;
      case "profile":
        return <Profile client={client} auth={auth} onNavigate={setActivePage} />;
      case "login":
      default:
        return <Login client={client} auth={auth} onNavigate={setActivePage} />;
    }
  })();

  if (isDemoMode) {
    return (
      <ErrorBoundary>
        <AppShell
          client={client}
          apiBaseUrl={apiBaseUrl}
          onApiBaseUrlChange={setApiBaseUrl}
          authWarning={null}
          health={resolvedHealth ?? null}
          config={resolvedConfig ?? null}
          activeBrand={activeBrand}
          activeOrganizationId={activeOrganizationId}
          activeTeamId={activeTeamId}
          brandProfile={brandProfile}
          brandValidation={brandValidation}
          brandDefaults={brandDefaults}
          currentUser={auth.currentUser}
          role={role}
          permissions={permissions}
          organizations={organizations}
          organizationProfile={organizationProfile}
          organizationContext={organizationContext}
          organizationTeams={organizationTeams}
          organizationMembers={organizationMembers}
          onLogout={async () => {
            await auth.logout();
          }}
          onNavigateProfile={() => setActivePage("profile")}
          onActiveBrandChange={setActiveBrand}
          onActiveOrganizationChange={setActiveOrganizationId}
          onActiveTeamChange={setActiveTeamId}
          activePage={effectivePage}
          onSelectPage={setActivePage}
          onRefreshHealth={refreshHealth}
          onRefreshConfig={refreshConfig}
        >
          {currentPage}
        </AppShell>
      </ErrorBoundary>
    );
  }

  if (!auth.loading && !auth.isAuthenticated) {
    return (
      <ErrorBoundary>
        <div className="auth-layout">{authOnlyPage}</div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
    <AppShell
      client={client}
      apiBaseUrl={apiBaseUrl}
      onApiBaseUrlChange={setApiBaseUrl}
      authWarning={authWarning}
      health={resolvedHealth ?? null}
      config={resolvedConfig ?? null}
      activeBrand={activeBrand}
      activeOrganizationId={activeOrganizationId}
      activeTeamId={activeTeamId}
      brandProfile={brandProfile}
      brandValidation={brandValidation}
      brandDefaults={brandDefaults}
      currentUser={auth.currentUser}
      role={role}
      permissions={permissions}
      organizations={organizations}
      organizationProfile={organizationProfile}
      organizationContext={organizationContext}
      organizationTeams={organizationTeams}
        organizationMembers={organizationMembers}
        onLogout={async () => {
        await auth.logout();
        setActivePage("login");
      }}
      onNavigateProfile={() => setActivePage("profile")}
      onActiveBrandChange={setActiveBrand}
      onActiveOrganizationChange={setActiveOrganizationId}
      onActiveTeamChange={setActiveTeamId}
      activePage={activePage}
      onSelectPage={setActivePage}
      onRefreshHealth={refreshHealth}
      onRefreshConfig={refreshConfig}
    >
      <AuthGuard isAuthenticated={auth.isAuthenticated} loading={auth.loading} onGoLogin={() => setActivePage("login")}>
        <div className="stack">
        {resolvedHealthLoading || resolvedConfigLoading ? (
          <Card>
            <SectionHeader title="Booting UI" description="Loading system health and configuration from the API." />
          </Card>
        ) : null}
        {resolvedHealthError || resolvedConfigError ? (
          <Card>
            <SectionHeader title="API Warning" description={resolvedHealthError || resolvedConfigError || ""} />
          </Card>
        ) : null}
        <PermissionGate
          permission={pagePermission || undefined}
          permissions={permissions}
          fallback={
            <EmptyState
              title="Access limited"
              description="Your current role does not allow access to this section."
              action={<Button type="button" variant="primary" onClick={() => setActivePage("dashboard")}>Back to Dashboard</Button>}
            />
          }
        >
        {currentPage}
        </PermissionGate>
        </div>
      </AuthGuard>
    </AppShell>
    </ErrorBoundary>
  );
}
