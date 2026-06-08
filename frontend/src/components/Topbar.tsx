import { useMemo } from "react";
import type { ApiClient } from "../api/client";
import type { BrandDefaults, BrandProfile, ConfigResponseData, HealthResponseData, MembershipProfile, OrganizationProfile, OrganizationRegistryEntry, TeamProfile, UserProfile } from "../types/api";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { BrandSelector } from "./BrandSelector";
import { OrganizationSwitcher } from "./OrganizationSwitcher";
import { TeamSelector } from "./TeamSelector";
import { UserMenu } from "./UserMenu";
import { StatusPill } from "./StatusPill";
import { getRoleLabel, getRoleTone } from "../utils/formatting";
import { IS_DEMO_MODE } from "../utils/demo";

interface TopbarProps {
  client: ApiClient;
  apiBaseUrl: string;
  onApiBaseUrlChange: (value: string) => void;
  authWarning?: string | null;
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
  onRefreshHealth: () => void;
  onRefreshConfig: () => void;
}

export function Topbar({
  client,
  apiBaseUrl,
  onApiBaseUrlChange,
  authWarning,
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
  onRefreshHealth,
  onRefreshConfig,
}: TopbarProps) {
  const status = health?.status ?? "unknown";
  const environment = config?.app_env ?? "development";
  const activeTeam = useMemo(() => organizationTeams?.find((team) => String(team.team_id ?? "") === activeTeamId) ?? null, [activeTeamId, organizationTeams]);
  const demoMode = IS_DEMO_MODE;

  return (
    <header className={`topbar${demoMode ? " topbar--demo" : ""}`}>
      <div className="topbar__row topbar__row--primary">
        <div className="topbar__brand">
          <h1 className="topbar__title">AI Marketing Content System</h1>
          <p className="topbar__subtitle">Frontend UI Platform</p>
        </div>
        <div className="topbar__primary-meta">
          <div className="topbar__field topbar__field--api">
            <label htmlFor="apiBaseUrl">API</label>
            <input id="apiBaseUrl" value={apiBaseUrl} onChange={(event) => onApiBaseUrlChange(event.target.value)} />
          </div>
          {demoMode ? <Badge tone="warning">Demo Mode</Badge> : null}
        </div>
      </div>
      <div className="topbar__row topbar__row--secondary">
        <div className="topbar__controls">
          <div className="topbar__field">
            <BrandSelector
              client={client}
              value={activeBrand}
              onChange={onActiveBrandChange}
              brandProfile={brandProfile ?? null}
              brandValidation={brandValidation ?? null}
              brandDefaults={brandDefaults ?? null}
              compact
            />
          </div>
          <div className="topbar__field">
            <OrganizationSwitcher
              client={client}
              value={activeOrganizationId}
              activeTeamId={activeTeam?.team_id ? String(activeTeam.team_id) : activeTeamId}
              activeTeamName={activeTeam?.name ? String(activeTeam.name) : activeTeamId}
              onChange={onActiveOrganizationChange}
              compact
            />
          </div>
          <div className="topbar__field">
            <TeamSelector
              client={client}
              organizationId={activeOrganizationId}
              value={activeTeamId}
              onChange={onActiveTeamChange}
              compact
            />
          </div>
        </div>
        <div className="topbar__meta">
          <StatusPill status={status} />
          <Badge tone="neutral">{brandProfile?.display_name ?? activeBrand}</Badge>
          <Badge tone="neutral">{organizationProfile?.name ?? activeOrganizationId ?? "No org"}</Badge>
          <Badge tone="neutral">{activeTeam?.name ?? activeTeamId ?? "No team"}</Badge>
        </div>
      </div>
    </header>
  );
}
