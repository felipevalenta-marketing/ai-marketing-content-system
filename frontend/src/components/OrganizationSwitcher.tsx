import { useEffect, useMemo, useState } from "react";
import type { ApiClient } from "../api/client";
import type { OrganizationRegistryEntry } from "../types/api";
import { Badge } from "./Badge";
import { LoadingState } from "./LoadingState";

interface OrganizationSwitcherProps {
  client: ApiClient;
  value: string;
  activeTeamId?: string;
  activeTeamName?: string;
  onChange: (value: string) => void;
  onLoaded?: (organizations: OrganizationRegistryEntry[]) => void;
  onSelectProfile?: (organization: OrganizationRegistryEntry | null) => void;
}

export function OrganizationSwitcher({ client, value, activeTeamId, activeTeamName, onChange, onLoaded, onSelectProfile }: OrganizationSwitcherProps) {
  const [organizations, setOrganizations] = useState<OrganizationRegistryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    client.getOrganizations().then((response) => {
      if (!active) return;
      if (response.success && response.data?.organizations) {
        const entries = response.data.organizations as OrganizationRegistryEntry[];
        setOrganizations(entries);
        onLoaded?.(entries);
        const selected = entries.find((item) => item.organization_id === value) ?? entries[0] ?? null;
        onSelectProfile?.(selected);
        if (!value && selected?.organization_id) {
          onChange(String(selected.organization_id));
        }
      } else {
        setOrganizations([]);
        setError(response.errors?.[0] ?? "No organizations available.");
        onSelectProfile?.(null);
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [client, onChange, onLoaded, onSelectProfile, value]);

  const selected = useMemo(() => organizations.find((item) => item.organization_id === value) ?? null, [organizations, value]);

  if (loading) {
    return <LoadingState label="Loading organizations..." />;
  }

  if (!organizations.length) {
    return <p className="muted">{error || "Create an organization to start."}</p>;
  }

  return (
    <div className="stack">
      <label className="field">
        <span>Organization</span>
        <select className="select" value={value || organizations[0]?.organization_id || ""} onChange={(event) => onChange(event.target.value)}>
          {organizations.map((organization) => (
            <option key={String(organization.organization_id)} value={String(organization.organization_id)}>
              {String(organization.name ?? organization.organization_id)}
            </option>
          ))}
        </select>
      </label>
      <div className="row wrap">
        <Badge tone={selected?.status === "inactive" ? "warning" : selected?.status === "suspended" ? "error" : "success"}>{String(selected?.status ?? "active")}</Badge>
        {typeof selected?.health_score === "number" ? <Badge tone={selected.health_score >= 80 ? "success" : selected.health_score >= 50 ? "warning" : "error"}>{`${selected.health_score}/100`}</Badge> : null}
        <Badge tone="neutral">{activeTeamName ?? activeTeamId ?? "No team"}</Badge>
        <span className="muted">{String(selected?.name ?? selected?.organization_id ?? value)}</span>
      </div>
    </div>
  );
}
