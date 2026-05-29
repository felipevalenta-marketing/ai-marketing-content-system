import type { ConfigResponseData, HealthResponseData } from "../types/api";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { StatusPill } from "./StatusPill";

interface TopbarProps {
  apiBaseUrl: string;
  onApiBaseUrlChange: (value: string) => void;
  health: HealthResponseData | null;
  config: ConfigResponseData | null;
  onRefreshHealth: () => void;
  onRefreshConfig: () => void;
}

export function Topbar({
  apiBaseUrl,
  onApiBaseUrlChange,
  health,
  config,
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
        <div className="topbar__meta">
          <StatusPill status={status} />
          <Badge tone="neutral">{environment}</Badge>
          <Button type="button" variant="secondary" onClick={onRefreshHealth}>
            Refresh Health
          </Button>
          <Button type="button" variant="secondary" onClick={onRefreshConfig}>
            Refresh Config
          </Button>
        </div>
      </div>
    </header>
  );
}
