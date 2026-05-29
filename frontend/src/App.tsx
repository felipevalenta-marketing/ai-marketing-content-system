import { useState } from "react";
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
import type { SnapshotStore } from "./pages/shared";
import { useApi } from "./hooks/useApi";
import { useConfig } from "./hooks/useConfig";
import { useHealth } from "./hooks/useHealth";
import { useLocalState } from "./hooks/useLocalState";
import { Card } from "./components/Card";
import { SectionHeader } from "./components/SectionHeader";

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
  | "config";

const SNAPSHOT_DEFAULT: SnapshotStore = {};

export default function App() {
  const { apiBaseUrl, setApiBaseUrl, client } = useApi();
  const { data: health, loading: healthLoading, error: healthError, refresh: refreshHealth } = useHealth(apiBaseUrl);
  const { data: config, loading: configLoading, error: configError, refresh: refreshConfig } = useConfig(apiBaseUrl);
  const [activePage, setActivePage] = useLocalState<PageKey>("amcs:active-page", "dashboard");
  const [snapshots, setSnapshots] = useLocalState<SnapshotStore>("amcs:snapshots", SNAPSHOT_DEFAULT);

  const onSnapshot = (key: string, data: unknown) => {
    setSnapshots((current) => ({
      ...current,
      [key]: { timestamp: new Date().toISOString(), data },
    }));
  };

  const currentPage = (() => {
    const pageProps = { client, snapshots, onSnapshot, health: health ?? null, config: config ?? null };
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
      case "dashboard":
      default:
        return <Dashboard {...pageProps} onNavigate={setActivePage} onCheckHealth={refreshHealth} />;
    }
  })();

  return (
    <AppShell
      apiBaseUrl={apiBaseUrl}
      onApiBaseUrlChange={setApiBaseUrl}
      health={health ?? null}
      config={config ?? null}
      activePage={activePage}
      onSelectPage={setActivePage}
      onRefreshHealth={refreshHealth}
      onRefreshConfig={refreshConfig}
    >
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
        {currentPage}
      </div>
    </AppShell>
  );
}
