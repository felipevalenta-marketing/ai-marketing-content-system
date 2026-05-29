import type { ReactNode } from "react";
import type { ConfigResponseData, HealthResponseData } from "../types/api";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

interface AppShellProps {
  children: ReactNode;
  apiBaseUrl: string;
  onApiBaseUrlChange: (value: string) => void;
  health: HealthResponseData | null;
  config: ConfigResponseData | null;
  activePage: string;
  onSelectPage: (page: string) => void;
  onRefreshConfig: () => void;
  onRefreshHealth: () => void;
}

export function AppShell({
  children,
  apiBaseUrl,
  onApiBaseUrlChange,
  health,
  config,
  activePage,
  onSelectPage,
  onRefreshConfig,
  onRefreshHealth,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <Topbar
        apiBaseUrl={apiBaseUrl}
        onApiBaseUrlChange={onApiBaseUrlChange}
        health={health}
        config={config}
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
