import { useEffect, useMemo, useRef, useState } from "react";
import { isUnauthorizedResponse, type ApiClient } from "../api/client";
import type { OrganizationRegistryEntry } from "../types/api";
import { Badge } from "./Badge";
import { LoadingState } from "./LoadingState";
import { DEMO_ORGANIZATION_PROFILE, IS_DEMO_MODE } from "../utils/demo";

interface OrganizationSwitcherProps {
  client: ApiClient;
  value: string;
  activeTeamId?: string;
  activeTeamName?: string;
  onChange: (value: string) => void;
  onLoaded?: (organizations: OrganizationRegistryEntry[]) => void;
  onSelectProfile?: (organization: OrganizationRegistryEntry | null) => void;
  compact?: boolean;
}

export function OrganizationSwitcher({ client, value, activeTeamId, activeTeamName, onChange, onLoaded, onSelectProfile, compact = false }: OrganizationSwitcherProps) {
  const [organizations, setOrganizations] = useState<OrganizationRegistryEntry[]>(() => (IS_DEMO_MODE ? ([DEMO_ORGANIZATION_PROFILE] as OrganizationRegistryEntry[]) : []));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const hasLoadedRef = useRef(IS_DEMO_MODE);
  const onLoadedRef = useRef(onLoaded);
  const onSelectProfileRef = useRef(onSelectProfile);

  useEffect(() => {
    onLoadedRef.current = onLoaded;
  }, [onLoaded]);

  useEffect(() => {
    onSelectProfileRef.current = onSelectProfile;
  }, [onSelectProfile]);

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    let active = true;
    setLoading(true);
    (async () => {
      try {
        const response = await client.getOrganizations();
        if (!active) return;
        if (response.success && response.data?.organizations) {
          const entries = response.data.organizations as OrganizationRegistryEntry[];
          setOrganizations(entries);
          onLoadedRef.current?.(entries);
          const selected = entries.find((item) => item.organization_id === value) ?? entries[0] ?? null;
          onSelectProfileRef.current?.(selected);
          if (!value && selected?.organization_id) {
            onChange(String(selected.organization_id));
          }
        } else {
          setOrganizations([]);
          setError(isUnauthorizedResponse(response) ? "Your session expired. Please log in again." : response.errors?.[0] ?? "No organizations available.");
          onSelectProfileRef.current?.(null);
        }
      } catch (loadError) {
        if (!active) {
          return;
        }
        setOrganizations([]);
        setError(loadError instanceof Error ? loadError.message : "No organizations available.");
        onSelectProfileRef.current?.(null);
      } finally {
        if (active) {
          hasLoadedRef.current = true;
          setLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [client]);

  useEffect(() => {
    if (!organizations.length) {
      return;
    }
    const selected = organizations.find((item) => item.organization_id === value) ?? null;
    if (!selected?.organization_id) {
      const fallback = organizations[0]?.organization_id ? String(organizations[0].organization_id) : "";
      if (fallback && fallback !== value) {
        onChange(fallback);
      }
    }
    onSelectProfile?.(selected ?? organizations[0] ?? null);
  }, [organizations, onChange, onSelectProfile, value]);

  const selected = useMemo(() => organizations.find((item) => item.organization_id === value) ?? null, [organizations, value]);

  if (loading && !hasLoadedRef.current) {
    return <LoadingState label="Loading organizations..." />;
  }

  if (!organizations.length) {
    if (compact) {
      return (
        <select className="select topbar__select" value={value || ""} onChange={(event) => onChange(event.target.value)}>
          <option value={value || ""}>{value || "No organizations available."}</option>
        </select>
      );
    }
    return <p className="muted">{error || "No organizations available."}</p>;
  }

  if (compact) {
    return (
      <select className="select topbar__select" value={value || organizations[0]?.organization_id || ""} onChange={(event) => onChange(event.target.value)}>
        {organizations.map((organization) => (
          <option key={String(organization.organization_id)} value={String(organization.organization_id)}>
            {String(organization.name ?? organization.organization_id)}
          </option>
        ))}
      </select>
    );
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
