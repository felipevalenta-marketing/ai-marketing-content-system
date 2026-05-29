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
import type { AnalyticsDashboardData, AnalyticsHealthData, AnalyticsSummaryData, BrandDefaults, BrandProfile, BrandRegistryEntry } from "./types/api";
import { createApiClient } from "./api/client";

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
  const { data: health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(apiBaseUrl);
  const { data: config, loading: configLoading, error: configError, refresh: refreshConfig } = useConfig(apiBaseUrl);
  const [activePage, setActivePage] = useLocalState<PageKey>("amcs:active-page", "dashboard");
  const [activeBrand, setActiveBrand] = useLocalState<string>("amcs:active-brand", "wenzel_partner");
  const [snapshots, setSnapshots] = useLocalState<SnapshotStore>("amcs:snapshots", SNAPSHOT_DEFAULT);
  const [brands, setBrands] = useState<BrandRegistryEntry[]>([]);
  const [brandProfile, setBrandProfile] = useState<BrandProfile | null>(null);
  const [brandValidation, setBrandValidation] = useState<Record<string, unknown> | null>(null);
  const [brandDefaults, setBrandDefaults] = useState<BrandDefaults | null>(null);
  const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummaryData | null>(null);
  const [analyticsDashboard, setAnalyticsDashboard] = useState<AnalyticsDashboardData | null>(null);
  const [analyticsHealth, setAnalyticsHealth] = useState<AnalyticsHealthData | null>(null);
  const permissions = auth.permissions;
  const role = auth.role;

  useEffect(() => {
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
  }, [apiBaseUrl]);

  useEffect(() => {
    let active = true;
    client.getBrands().then((response) => {
      if (!active) {
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
  }, [client, apiBaseUrl]);

  useEffect(() => {
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
        setBrandProfile(profileResponse.success && profileResponse.data ? (profileResponse.data as BrandProfile) : null);
        setBrandValidation(validationResponse.success && validationResponse.data ? (validationResponse.data as Record<string, unknown>) : null);
        const defaultsPayload = defaultsResponse.success && defaultsResponse.data ? (defaultsResponse.data as Record<string, unknown>) : null;
        setBrandDefaults((defaultsPayload?.defaults as BrandDefaults) ?? null);
      },
    );
    return () => {
      active = false;
    };
  }, [activeBrand, client]);

  useEffect(() => {
    if (!activeBrand && config?.default_brand) {
      setActiveBrand(String(config.default_brand));
    }
  }, [activeBrand, config?.default_brand, setActiveBrand]);

  useEffect(() => {
    if (!auth.loading && !auth.isAuthenticated && activePage !== "login" && activePage !== "register") {
      setActivePage("login");
    }
  }, [activePage, auth.isAuthenticated, auth.loading, setActivePage]);

  useEffect(() => {
    if (auth.isAuthenticated && (activePage === "login" || activePage === "register")) {
      setActivePage("dashboard");
    }
  }, [activePage, auth.isAuthenticated, setActivePage]);

  useEffect(() => {
    if (auth.isAuthenticated) {
      void refreshConfig();
    }
  }, [auth.isAuthenticated, refreshConfig]);

  useEffect(() => {
    if (!brands.length) {
      return;
    }
    const available = brands.find((brand) => brand.brand_id === activeBrand);
    if (!available) {
      const fallback = brands.find((brand) => brand.brand_id === config?.default_brand)?.brand_id ?? brands[0]?.brand_id;
      if (fallback && fallback !== activeBrand) {
        setActiveBrand(String(fallback));
      }
    }
  }, [activeBrand, brands, config?.default_brand, setActiveBrand]);

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
        health: health ?? null,
        config: config ?? null,
        role,
        permissions,
        activeBrand,
        brandProfile,
        brandValidation,
      brandDefaults,
      brands,
      analyticsSummary,
      analyticsDashboard,
      analyticsHealth,
    };
    switch (activePage) {
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
    switch (activePage) {
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
        return "";
      default:
        return "";
    }
  })();

  const authOnlyPage = (() => {
    switch (activePage) {
      case "register":
        return <Register client={client} auth={auth} onNavigate={setActivePage} />;
      case "profile":
        return <Profile client={client} auth={auth} onNavigate={setActivePage} />;
      case "login":
      default:
        return <Login client={client} auth={auth} onNavigate={setActivePage} />;
    }
  })();

  if (!auth.loading && !auth.isAuthenticated) {
    return <div className="auth-layout">{authOnlyPage}</div>;
  }

  return (
    <AppShell
      client={client}
      apiBaseUrl={apiBaseUrl}
      onApiBaseUrlChange={setApiBaseUrl}
      health={health ?? null}
      config={config ?? null}
      activeBrand={activeBrand}
      brandProfile={brandProfile}
      brandValidation={brandValidation}
      brandDefaults={brandDefaults}
      currentUser={auth.currentUser}
      role={role}
      permissions={permissions}
      onLogout={async () => {
        await auth.logout();
        setActivePage("login");
      }}
      onNavigateProfile={() => setActivePage("profile")}
      onActiveBrandChange={setActiveBrand}
      activePage={activePage}
      onSelectPage={setActivePage}
      onRefreshHealth={refreshHealth}
      onRefreshConfig={refreshConfig}
    >
      <AuthGuard isAuthenticated={auth.isAuthenticated} loading={auth.loading} onGoLogin={() => setActivePage("login")}>
        <div className="stack">
        {healthLoading || configLoading ? (
          <Card>
            <SectionHeader title="Booting UI" description="Loading system health and configuration from the API." />
          </Card>
        ) : null}
        {healthError || configError ? (
          <Card>
            <SectionHeader title="API Warning" description={healthError || configError || ""} />
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
  );
}
