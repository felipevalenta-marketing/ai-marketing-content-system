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

interface TopbarProps {
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
  onRefreshHealth: () => void;
  onRefreshConfig: () => void;
}

export function Topbar({
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
  onRefreshHealth,
  onRefreshConfig,
}: TopbarProps) {
  const status = health?.status ?? "unknown";
  const environment = config?.app_env ?? "development";
  const activeTeam = useMemo(() => organizationTeams?.find((team) => String(team.team_id ?? "") === activeTeamId) ?? null, [activeTeamId, organizationTeams]);

  return (
    <header className="topbar">
      <div className="topbar__brand">
        <h1 className="topbar__title">AI Marketing Content System</h1>
        <p className="topbar__subtitle">Frontend UI Platform</p>
      </div>
      <div className="topbar__controls">
        <div className="topbar__field">
          <label htmlFor="apiBaseUrl">API</label>
          <input id="apiBaseUrl" value={apiBaseUrl} onChange={(event) => onApiBaseUrlChange(event.target.value)} />
        </div>
        <div className="topbar__field">
          <label>Brand</label>
          <BrandSelector
            client={client}
            value={activeBrand}
            onChange={onActiveBrandChange}
            brandProfile={brandProfile ?? null}
            brandValidation={brandValidation ?? null}
            brandDefaults={brandDefaults ?? null}
          />
        </div>
        <div className="topbar__field">
          <label>Organization</label>
          <OrganizationSwitcher
            client={client}
            value={activeOrganizationId}
            activeTeamId={activeTeam?.team_id ? String(activeTeam.team_id) : activeTeamId}
            activeTeamName={activeTeam?.name ? String(activeTeam.name) : activeTeamId}
            onChange={onActiveOrganizationChange}
          />
        </div>
        <div className="topbar__field">
          <label>Team</label>
          <TeamSelector
            client={client}
            organizationId={activeOrganizationId}
            value={activeTeamId}
            onChange={onActiveTeamChange}
          />
        </div>
        <div className="topbar__meta">
          <StatusPill status={status} />
          <Badge tone="neutral">{environment}</Badge>
          <Badge tone={getRoleTone(role)}>{getRoleLabel(role)}</Badge>
          <Badge tone={brandProfile?.status === "partial" || brandProfile?.status === "incomplete" ? "warning" : brandProfile?.status === "invalid" ? "error" : "success"}>
            {brandProfile?.display_name ?? activeBrand}
          </Badge>
          {typeof brandProfile?.health_score === "number" ? <Badge tone={brandProfile.health_score >= 80 ? "success" : brandProfile.health_score >= 50 ? "warning" : "error"}>{`${brandProfile.health_score}/100`}</Badge> : null}
          <Badge tone="neutral">{organizationProfile?.name ?? activeOrganizationId ?? "No org"}</Badge>
          <Badge tone="neutral">{activeTeam?.name ?? activeTeamId ?? "No team"}</Badge>
          <Badge tone="neutral">{`${organizations?.length ?? 0} orgs`}</Badge>
          <Badge tone="neutral">{`${organizationTeams?.length ?? 0} teams`}</Badge>
          <Badge tone="neutral">{`${organizationMembers?.length ?? 0} members`}</Badge>
          <Button type="button" variant="secondary" onClick={onRefreshHealth}>
            Refresh Health
          </Button>
          <Button type="button" variant="secondary" onClick={onRefreshConfig}>
            Refresh Config
          </Button>
          <UserMenu user={currentUser ?? null} role={role} permissions={permissions} onProfile={onNavigateProfile ?? (() => undefined)} onLogout={onLogout ?? (() => undefined)} />
        </div>
      </div>
    </header>
  );
}
