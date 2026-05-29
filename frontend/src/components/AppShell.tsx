import type { ReactNode } from "react";
import type { ApiClient } from "../api/client";
import type { BrandDefaults, BrandProfile, ConfigResponseData, HealthResponseData } from "../types/api";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
  client: ApiClient;
  apiBaseUrl: string;
  onApiBaseUrlChange: (value: string) => void;
  health: HealthResponseData | null;
  config: ConfigResponseData | null;
  activeBrand: string;
  brandProfile?: BrandProfile | null;
  brandValidation?: Record<string, unknown> | null;
  brandDefaults?: BrandDefaults | null;
  onActiveBrandChange: (value: string) => void;
  activePage: string;
  onSelectPage: (page: string) => void;
  onRefreshConfig: () => void;
  onRefreshHealth: () => void;
}

export function AppShell({
  children,
  client,
  apiBaseUrl,
  onApiBaseUrlChange,
  health,
  config,
  activeBrand,
  brandProfile,
  brandValidation,
  brandDefaults,
  onActiveBrandChange,
  activePage,
  onSelectPage,
  onRefreshConfig,
  onRefreshHealth,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <Topbar
        client={client}
        apiBaseUrl={apiBaseUrl}
        onApiBaseUrlChange={onApiBaseUrlChange}
        health={health}
        config={config}
        activeBrand={activeBrand}
        brandProfile={brandProfile ?? null}
        brandValidation={brandValidation ?? null}
        brandDefaults={brandDefaults ?? null}
        onActiveBrandChange={onActiveBrandChange}
        onRefreshHealth={onRefreshHealth}
        onRefreshConfig={onRefreshConfig}
      />
      <div className="app-layout">
        <Sidebar activePage={activePage} onSelectPage={onSelectPage} config={config} />
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
