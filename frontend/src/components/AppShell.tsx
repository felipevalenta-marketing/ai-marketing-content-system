import type { ReactNode } from "react";
import type { ApiClient } from "../api/client";
import type { BrandDefaults, BrandProfile, ConfigResponseData, HealthResponseData, MembershipProfile, OrganizationProfile, OrganizationRegistryEntry, TeamProfile, UserProfile } from "../types/api";
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
  activeOrganizationId: string;
  activeTeamId: string;
  brandProfile?: BrandProfile | null;
  brandValidation?: Record<string, unknown> | null;
  brandDefaults?: BrandDefaults | null;
  currentUser?: UserProfile | null;
  role: string;
  permissions: string[];
  organizations?: OrganizationRegistryEntry[];
  organizationProfile?: OrganizationProfile | null;
  organizationTeams?: TeamProfile[];
  organizationMembers?: MembershipProfile[];
  onLogout?: () => void;
  onNavigateProfile?: () => void;
  onActiveBrandChange: (value: string) => void;
  onActiveOrganizationChange: (value: string) => void;
  onActiveTeamChange: (value: string) => void;
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
  activeOrganizationId,
  activeTeamId,
  brandProfile,
  brandValidation,
  brandDefaults,
  currentUser,
  role,
  permissions,
  organizations,
  organizationProfile,
  organizationTeams,
  organizationMembers,
  onLogout,
  onNavigateProfile,
  onActiveBrandChange,
  onActiveOrganizationChange,
  onActiveTeamChange,
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
        activeOrganizationId={activeOrganizationId}
        activeTeamId={activeTeamId}
        brandProfile={brandProfile ?? null}
        brandValidation={brandValidation ?? null}
        brandDefaults={brandDefaults ?? null}
        currentUser={currentUser ?? null}
        onLogout={onLogout}
        onNavigateProfile={onNavigateProfile}
        onActiveBrandChange={onActiveBrandChange}
        onActiveOrganizationChange={onActiveOrganizationChange}
        onActiveTeamChange={onActiveTeamChange}
        onRefreshHealth={onRefreshHealth}
        onRefreshConfig={onRefreshConfig}
        organizations={organizations ?? []}
        organizationProfile={organizationProfile ?? null}
        organizationTeams={organizationTeams ?? []}
        organizationMembers={organizationMembers ?? []}
      />
      <div className="app-layout">
        <Sidebar activePage={activePage} onSelectPage={onSelectPage} config={config} role={role} permissions={permissions} activeOrganizationId={activeOrganizationId} activeTeamId={activeTeamId} />
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
