import type { ApiClient } from "../api/client";
import type { BrandDefaults, BrandProfile, ConfigResponseData, HealthResponseData, UserProfile } from "../types/api";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { BrandSelector } from "./BrandSelector";
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
  brandProfile?: BrandProfile | null;
  brandValidation?: Record<string, unknown> | null;
  brandDefaults?: BrandDefaults | null;
  currentUser?: UserProfile | null;
  role: string;
  permissions: string[];
  onLogout?: () => void;
  onNavigateProfile?: () => void;
  onActiveBrandChange: (value: string) => void;
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
  brandProfile,
  brandValidation,
  brandDefaults,
  currentUser,
  role,
  permissions,
  onLogout,
  onNavigateProfile,
  onActiveBrandChange,
  onRefreshHealth,
  onRefreshConfig,
}: TopbarProps) {
  const status = health?.status ?? "unknown";
  const environment = config?.app_env ?? "development";

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
        <div className="topbar__meta">
          <StatusPill status={status} />
          <Badge tone="neutral">{environment}</Badge>
          <Badge tone={getRoleTone(role)}>{getRoleLabel(role)}</Badge>
          <Badge tone={brandProfile?.status === "partial" || brandProfile?.status === "incomplete" ? "warning" : brandProfile?.status === "invalid" ? "error" : "success"}>
            {brandProfile?.display_name ?? activeBrand}
          </Badge>
          {typeof brandProfile?.health_score === "number" ? <Badge tone={brandProfile.health_score >= 80 ? "success" : brandProfile.health_score >= 50 ? "warning" : "error"}>{`${brandProfile.health_score}/100`}</Badge> : null}
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
