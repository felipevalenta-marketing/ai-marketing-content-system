import { useEffect, useMemo, useState } from "react";
import { isUnauthorizedResponse, type ApiClient } from "../api/client";
import type { TeamProfile } from "../types/api";
import { LoadingState } from "./LoadingState";
import { Badge } from "./Badge";
import { DEMO_TEAMS, IS_DEMO_MODE } from "../utils/demo";

interface TeamSelectorProps {
  client: ApiClient;
  organizationId: string;
  value: string;
  onChange: (value: string) => void;
  onLoaded?: (teams: TeamProfile[]) => void;
  compact?: boolean;
}

export function TeamSelector({ client, organizationId, value, onChange, onLoaded, compact = false }: TeamSelectorProps) {
  const [teams, setTeams] = useState<TeamProfile[]>(() => (IS_DEMO_MODE ? (DEMO_TEAMS as TeamProfile[]) : []));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (IS_DEMO_MODE) {
      return;
    }
    if (!organizationId) {
      setTeams([]);
      return;
    }
    let active = true;
    setLoading(true);
    client.getOrganizationTeams(organizationId).then((response) => {
      if (!active) return;
      if (response.success && response.data?.teams) {
        const entries = response.data.teams as TeamProfile[];
        setTeams(entries);
        onLoaded?.(entries);
        const selected = entries.find((item) => item.team_id === value);
        if (!selected && entries[0]?.team_id) {
          onChange(String(entries[0].team_id));
        }
      } else {
        setTeams([]);
        setError(isUnauthorizedResponse(response) ? "Your session expired. Please log in again." : response.errors?.[0] ?? "No teams available.");
      }
      setLoading(false);
    });
    return () => {
      active = false;
    };
  }, [client, onLoaded, organizationId]);

  useEffect(() => {
    if (!teams.length) {
      return;
    }
    const selected = teams.find((item) => item.team_id === value) ?? null;
    if (!selected?.team_id) {
      const fallback = teams[0]?.team_id ? String(teams[0].team_id) : "";
      if (fallback && fallback !== value) {
        onChange(fallback);
      }
    }
  }, [onChange, teams, value]);

  const selected = useMemo(() => teams.find((item) => item.team_id === value) ?? null, [teams, value]);

  if (!organizationId) {
    return <p className="muted">Select an organization to view teams.</p>;
  }

  if (loading) {
    return <LoadingState label="Loading teams..." />;
  }

  if (!teams.length) {
    if (compact) {
      return (
        <select className="select topbar__select" value={value || ""} onChange={(event) => onChange(event.target.value)}>
          <option value={value || ""}>{value || "No teams found"}</option>
        </select>
      );
    }
    return <p className="muted">{error || "No teams found for this organization."}</p>;
  }

  if (compact) {
    return (
      <select className="select topbar__select" value={value || teams[0]?.team_id || ""} onChange={(event) => onChange(event.target.value)}>
        {teams.map((team) => (
          <option key={String(team.team_id)} value={String(team.team_id)}>
            {String(team.name ?? team.team_id)}
          </option>
        ))}
      </select>
    );
  }

  return (
    <div className="stack">
      <label className="field">
        <span>Team</span>
        <select className="select" value={value || teams[0]?.team_id || ""} onChange={(event) => onChange(event.target.value)}>
          {teams.map((team) => (
            <option key={String(team.team_id)} value={String(team.team_id)}>
              {String(team.name ?? team.team_id)}
            </option>
          ))}
        </select>
      </label>
      <div className="row wrap">
        <Badge tone={selected?.status === "inactive" ? "warning" : selected?.status === "archived" ? "error" : "success"}>{String(selected?.status ?? "active")}</Badge>
        <span className="muted">{String(selected?.name ?? selected?.team_id ?? value)}</span>
      </div>
    </div>
  );
}
