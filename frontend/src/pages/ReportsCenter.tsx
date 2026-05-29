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
import { REPORT_TYPES } from "../api/endpoints";
import type { MarkdownReportRequest } from "../types/api";
import type { MarkdownReportData } from "../types/reports";
import type { WorkspaceProps } from "./shared";
import { getSnapshotChain } from "./shared";
import { extractMarkdown } from "../utils/formatting";
import { useLocalState } from "../hooks/useLocalState";

interface ReportsCenterProps extends WorkspaceProps {
  onSnapshot: (key: string, data: unknown) => void;
}

type ReportSource = "latest" | "snapshot";

const DEFAULT_FORM: MarkdownReportRequest = {
  report_type: "workflow_report",
  title: "Campaign Workflow Report",
};

export function ReportsCenter({ client, snapshots, onSnapshot, analyticsSummary, activeBrand, activeOrganizationId, activeTeamId }: ReportsCenterProps) {
  const [form, setForm] = useLocalState<MarkdownReportRequest>("amcs:report-form", DEFAULT_FORM);
  const [reportSource, setReportSource] = useState<ReportSource>("snapshot");
  const [result, setResult] = useState<any>(null);
  const [latestReport, setLatestReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [latestLoading, setLatestLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setLatestLoading(true);
    client.getLatestReports().then((response) => {
      if (response.success && response.data) {
        setLatestReport(response.data as any);
      }
      setLatestLoading(false);
    });
  }, [client.baseUrl]);

  const buildPayload = (): MarkdownReportRequest => {
    if (reportSource === "latest" && latestReport) {
      return {
        ...form,
        ...latestReport,
        report_type: String(form.report_type ?? latestReport.report_type ?? "workflow_report"),
        title: String(form.title ?? latestReport.title ?? "Markdown Report"),
      };
    }
    const workflowResult = getSnapshotChain<any>(snapshots, ["workflow", "generate", "campaign", "assets"]);
    const workflowSummary = workflowResult as any;
    return {
      ...form,
      brand: activeBrand ?? form.brand,
      organization_id: activeOrganizationId ?? form.organization_id ?? "",
      team_id: activeTeamId ?? form.team_id ?? "",
      workflow_result: workflowSummary ?? undefined,
      pipeline_result: getSnapshotChain<any>(snapshots, ["generate", "workflow"]) ?? undefined,
      campaign_result: getSnapshotChain<any>(snapshots, ["campaign"]) ?? undefined,
      asset_result: getSnapshotChain<any>(snapshots, ["assets"]) ?? undefined,
      governance_result: getSnapshotChain<any>(snapshots, ["workflow", "generate", "campaign", "assets"]) ?? undefined,
      token_summary: (getSnapshotChain<any>(snapshots, ["workflow", "generate"]) as any)?.token_summary ?? undefined,
      cost_summary: (getSnapshotChain<any>(snapshots, ["workflow", "generate"]) as any)?.cost_summary ?? undefined,
      storage_summary: (getSnapshotChain<any>(snapshots, ["workflow", "generate"]) as any)?.storage_summary ?? undefined,
      report_type: String(form.report_type ?? "workflow_report"),
      title: String(form.title ?? "Markdown Report"),
    };
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.generateMarkdownReport(buildPayload());
    if (response.success && response.data) {
      const data = response.data as MarkdownReportData;
      setResult(data);
      onSnapshot("reports", data);
    } else {
      setError(response.errors?.[0] ?? "Unable to generate markdown report.");
      setResult(null);
    }
    setLoading(false);
  };

  const markdown = extractMarkdown(result);

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader title="Reports Center" description="Generate and preview markdown reports from structured payloads." />
        <div className="row wrap">
          <span className="muted">Organization: {activeOrganizationId || "All"}</span>
          <span className="muted">Team: {activeTeamId || "All"}</span>
        </div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="report_type">Report Type</label>
            <select id="report_type" className="select" value={String(form.report_type ?? "workflow_report")} onChange={(event) => setForm((current) => ({ ...current, report_type: event.target.value } as MarkdownReportRequest))}>
              {REPORT_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="title">Title</label>
            <input id="title" className="input" value={String(form.title ?? "")} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value } as MarkdownReportRequest))} />
          </div>
          <div className="field field--full">
            <label>Source</label>
            <div className="button-row">
              <Button type="button" variant={reportSource === "snapshot" ? "primary" : "secondary"} onClick={() => setReportSource("snapshot")}>Use Workspace Snapshot</Button>
              <Button type="button" variant={reportSource === "latest" ? "primary" : "secondary"} onClick={() => setReportSource("latest")}>Use Latest Report</Button>
            </div>
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Rendering..." : "Generate Markdown"}
          </Button>
        </div>
        {loading ? <LoadingState label="Rendering markdown report..." /> : null}
        {error ? <ErrorState message={error} /> : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Report Preview" description="Latest report metadata and the generated markdown output." />
        {analyticsSummary ? (
          <div className="section">
            <StatusPill status={String((analyticsSummary.executive_summary as any)?.approval_status ?? "review")} />
            <p><strong>Analytics:</strong> {String((analyticsSummary.executive_summary as any)?.headline ?? "Ready")}</p>
          </div>
        ) : null}
        {latestLoading ? <LoadingState label="Loading latest report..." /> : null}
        {latestReport ? (
          <div className="section">
            <StatusPill status={String(latestReport.report_type ?? "report")} />
            <p><strong>Latest Report:</strong> {String(latestReport.title ?? latestReport.report_type ?? "-")}</p>
          </div>
        ) : null}
        {result ? (
          <div className="result-panel">
            <MarkdownPreview markdown={markdown} />
            <JsonViewer data={result} title="Report JSON" />
          </div>
        ) : (
          <EmptyState title="No report generated yet" description="Render a markdown report to preview the clean, client-ready output." />
        )}
      </Card>
    </div>
  );
}
