import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { MarkdownPreview } from "../components/MarkdownPreview";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { ASSET_DEFAULTS } from "../utils/constants";
import { extractMarkdown, joinList } from "../utils/formatting";
import type { AssetRequest } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";

interface AssetStudioProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

const DEFAULT_FORM: AssetRequest = { ...ASSET_DEFAULTS };

export function AssetStudio({ client, onSnapshot, activeBrand }: AssetStudioProps) {
  const [form, setForm] = useLocalState<AssetRequest>("amcs:assets-form", DEFAULT_FORM);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeBrand && activeBrand !== form.brand) {
      setForm((current) => ({ ...current, brand: activeBrand } as AssetRequest));
    }
  }, [activeBrand, form.brand, setForm]);

  const update = (key: keyof AssetRequest, value: unknown) => {
    setForm((current) => ({ ...current, [key]: value } as AssetRequest));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.runAssets(form);
    if (response.success && response.data) {
      const data = response.data as any;
      setResult(data);
      onSnapshot("assets", data);
    } else {
      setError(response.errors?.[0] ?? "Unable to coordinate assets.");
      setResult(null);
    }
    setLoading(false);
  };

  const markdown = extractMarkdown(result);

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader title="Asset Studio" description="Coordinate asset plans, prompts, and readiness guidance." />
        <div className="form-grid">
          {[
            ["brand", "Brand"],
            ["platform", "Platform"],
            ["content_type", "Content Type"],
            ["campaign_type", "Campaign Type"],
            ["objective", "Objective"],
            ["visual_style", "Visual Style"],
          ].map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <input id={key} className="input" value={String(form[key as keyof AssetRequest] ?? "")} onChange={(event) => update(key as keyof AssetRequest, event.target.value)} />
            </div>
          ))}
          <div className="field field--full">
            <label htmlFor="assets">Assets</label>
            <input id="assets" className="input" value={joinList(form.assets)} onChange={(event) => update("assets", event.target.value.split(",").map((item) => item.trim()).filter(Boolean))} />
          </div>
          <div className="field field--full">
            <label htmlFor="creative_direction">Creative Direction</label>
            <textarea id="creative_direction" className="textarea" value={String(form.creative_direction ?? "")} onChange={(event) => update("creative_direction", event.target.value)} />
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Coordinating..." : "Run Assets"}
          </Button>
        </div>
        {loading ? <LoadingState label="Coordinating assets..." /> : null}
        {error ? <ErrorState message={error} /> : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Asset Result" description="Asset plan, missing assets, readiness, and prompt/script outputs." />
        {result ? (
          <div className="result-panel">
            <StatusPill status={String(result.status ?? "completed")} />
            <p><strong>Missing Assets:</strong> {joinList((result.missing_assets as string[] | undefined) ?? [])}</p>
            <p><strong>Readiness:</strong> {String(result.readiness_status ?? result.asset_readiness ?? "-")}</p>
            {markdown ? <MarkdownPreview markdown={markdown} /> : null}
            <JsonViewer data={result} title="Safe JSON" />
          </div>
        ) : (
          <EmptyState title="No asset result yet" description="Run asset coordination to preview prompt readiness and missing assets." />
        )}
      </Card>
    </div>
  );
}
