import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { CAMPAIGN_DEFAULTS } from "../utils/constants";
import { joinList } from "../utils/formatting";
import type { CampaignRequest } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";

interface CampaignStudioProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

const DEFAULT_FORM: CampaignRequest = { ...CAMPAIGN_DEFAULTS };

export function CampaignStudio({ client, onSnapshot, activeBrand, activeOrganizationId, activeTeamId }: CampaignStudioProps) {
  const [form, setForm] = useLocalState<CampaignRequest>("amcs:campaign-form", DEFAULT_FORM);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeBrand && activeBrand !== form.brand) {
      setForm((current) => ({ ...current, brand: activeBrand } as CampaignRequest));
    }
  }, [activeBrand, form.brand, setForm]);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      organization_id: activeOrganizationId ?? "",
      team_id: activeTeamId ?? "",
    } as CampaignRequest));
  }, [activeOrganizationId, activeTeamId, setForm]);

  const update = (key: keyof CampaignRequest, value: unknown) => {
    setForm((current) => ({ ...current, [key]: value } as CampaignRequest));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.runCampaign(form);
    if (response.success && response.data) {
      const data = response.data as any;
      setResult(data);
      onSnapshot("campaign", data);
    } else {
      setError(response.errors?.[0] ?? "Campaign composition is unavailable.");
      setResult(null);
    }
    setLoading(false);
  };

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader title="Campaign Studio" description="Compose campaigns using the existing backend campaign composer." />
        <div className="form-grid">
          {[
            ["brand", "Brand"],
            ["platform", "Platform"],
            ["campaign_type", "Campaign Type"],
            ["objective", "Objective"],
            ["audience", "Audience"],
            ["location", "Location"],
            ["property_type", "Property Type"],
          ].map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <input id={key} className="input" value={String(form[key as keyof CampaignRequest] ?? "")} onChange={(event) => update(key as keyof CampaignRequest, event.target.value)} />
            </div>
          ))}
          <div className="field field--full">
            <label htmlFor="platforms">Platforms</label>
            <input id="platforms" className="input" value={joinList(form.platforms)} onChange={(event) => update("platforms", event.target.value.split(",").map((item) => item.trim()).filter(Boolean))} />
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Composing..." : "Run Campaign"}
          </Button>
        </div>
        {loading ? <LoadingState label="Composing campaign..." /> : null}
        {error ? <ErrorState message={error} /> : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Campaign Result" description="Strategy, deliverables, asset mapping, and governance status." />
        {result ? (
          <div className="result-panel">
            <StatusPill status={String(result.status ?? result.approval_status ?? "completed")} />
            <p><strong>Campaign:</strong> {String(result.campaign_name ?? result.campaign_type ?? "-")}</p>
            <p><strong>Strategy:</strong> {String((result.strategy as any)?.summary ?? "-")}</p>
            <p><strong>Deliverables:</strong> {String(((result.content_deliverables as any) ?? []).length ?? 0)}</p>
            <JsonViewer data={result} title="Safe JSON" />
          </div>
        ) : (
          <EmptyState title="No campaign result yet" description="Run campaign composition to preview the structured output." />
        )}
      </Card>
    </div>
  );
}
