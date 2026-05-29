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
import { WORKFLOW_DEFAULTS } from "../utils/constants";
import { extractMarkdown, formatCount, getStatusLabel, joinList } from "../utils/formatting";
import type { WorkflowRequest } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";
import type { WorkflowResult } from "../types/api";

interface WorkflowCenterProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

const DEFAULT_FORM: WorkflowRequest = {
  ...WORKFLOW_DEFAULTS,
  report: true,
  persist: false,
  dry_run: true,
};

export function WorkflowCenter({ client, onSnapshot, analyticsSummary, activeBrand, activeOrganizationId, activeTeamId }: WorkflowCenterProps) {
  const [form, setForm] = useLocalState<WorkflowRequest>("amcs:workflow-form", DEFAULT_FORM);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (activeBrand && activeBrand !== form.brand) {
      setForm((current) => ({ ...current, brand: activeBrand } as WorkflowRequest));
    }
  }, [activeBrand, form.brand, setForm]);

  useEffect(() => {
    setForm((current) => ({
      ...current,
      organization_id: activeOrganizationId ?? "",
      team_id: activeTeamId ?? "",
    } as WorkflowRequest));
  }, [activeOrganizationId, activeTeamId, setForm]);

  const update = (key: keyof WorkflowRequest, value: unknown) => {
    setForm((current) => ({ ...current, [key]: value } as WorkflowRequest));
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.runWorkflow(form);
    if (response.success && response.data) {
      const data = response.data as any;
      setResult(data);
      onSnapshot("workflow", data);
    } else {
      setError(response.errors?.[0] ?? "Unable to run workflow.");
      setResult(null);
    }
    setLoading(false);
  };

  const markdown = extractMarkdown(result);
  const steps = Array.isArray(result?.steps) ? result?.steps : [];

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader
          title="Workflow Center"
          description="Plan and run multi-step workflows with dry-run safety enabled by default."
          actions={<StatusPill status={String(result?.status ?? "planned")} />}
        />
        <div className="form-grid">
          {[
            ["workflow_type", "Workflow Type"],
            ["brand", "Brand"],
            ["platform", "Platform"],
            ["content_type", "Content Type"],
            ["campaign_type", "Campaign Type"],
            ["objective", "Objective"],
            ["audience", "Audience"],
            ["location", "Location"],
          ].map(([key, label]) => (
            <div className="field" key={key}>
              <label htmlFor={key}>{label}</label>
              <input id={key} className="input" value={String(form[key as keyof WorkflowRequest] ?? "")} onChange={(event) => update(key as keyof WorkflowRequest, event.target.value)} />
            </div>
          ))}
          <div className="field field--full">
            <label htmlFor="platforms">Platforms</label>
            <input id="platforms" className="input" value={joinList(form.platforms)} onChange={(event) => update("platforms", event.target.value.split(",").map((item) => item.trim()).filter(Boolean))} />
          </div>
          <div className="field field--full">
            <label htmlFor="assets">Assets</label>
            <input id="assets" className="input" value={joinList(form.assets)} onChange={(event) => update("assets", event.target.value.split(",").map((item) => item.trim()).filter(Boolean))} />
          </div>
          {[
            ["report", "Report"],
            ["persist", "Persist"],
            ["dry_run", "Dry Run"],
          ].map(([key, label]) => (
            <label className="field" key={key} style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: 10 }}>
              <input
                type="checkbox"
                checked={Boolean(form[key as keyof WorkflowRequest])}
                onChange={(event) => update(key as keyof WorkflowRequest, event.target.checked)}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Running..." : "Run Workflow"}
          </Button>
        </div>
        {loading ? <LoadingState label="Running workflow..." /> : null}
        {error ? <ErrorState message={error} /> : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Workflow Result" description="Status, step sequence, summaries, and report preview." />
        {result ? (
          <div className="result-panel">
            <StatusPill status={String(result.status ?? "completed")} />
            <p><strong>Workflow ID:</strong> {String(result.workflow_id ?? "-")}</p>
            <p><strong>Status:</strong> {getStatusLabel(String(result.status ?? "completed"))}</p>
            {analyticsSummary ? (
              <Card>
                <SectionHeader title="Analytics Snapshot" description="Live executive summary from the analytics layer." />
                <p><strong>{String((analyticsSummary.executive_summary as any)?.headline ?? "Analytics ready")}</strong></p>
                <p>{String((analyticsSummary.executive_summary as any)?.outcome ?? "")}</p>
              </Card>
            ) : null}
            <div className="grid-2">
              <div className="metric-card">
                <p className="metric-card__label">Completed</p>
                <p className="metric-card__value">{formatCount(result.summary?.completed_steps ?? 0)}</p>
              </div>
              <div className="metric-card">
                <p className="metric-card__label">Skipped</p>
                <p className="metric-card__value">{formatCount(result.summary?.skipped_steps ?? 0)}</p>
              </div>
            </div>
            {steps.length > 0 ? (
              <div className="section">
                {steps.map((step, index) => (
                  <div key={String((step as Record<string, unknown>).step_id ?? index)} className="metric-card">
                    <p className="metric-card__label">{String((step as Record<string, unknown>).name ?? `Step ${index + 1}`)}</p>
                    <p className="metric-card__value">{String((step as Record<string, unknown>).status ?? "planned")}</p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No step details" description="This workflow did not include step details." />
            )}
            {markdown ? <MarkdownPreview markdown={markdown} /> : null}
            <JsonViewer data={result} title="Safe JSON" />
          </div>
        ) : (
          <EmptyState title="No workflow result yet" description="Run a workflow to preview status, steps, and summaries." />
        )}
      </Card>
    </div>
  );
}
