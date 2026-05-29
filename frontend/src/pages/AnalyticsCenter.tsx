import { useEffect, useMemo, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { JsonViewer } from "../components/JsonViewer";
import { LoadingState } from "../components/LoadingState";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { ANALYTICS_DEFAULTS } from "../utils/constants";
import { formatCount, formatCurrency, formatPercent } from "../utils/formatting";
import type { AnalyticsRequest, AnalyticsResult } from "../types/api";
import type { WorkspaceProps } from "./shared";
import { useLocalState } from "../hooks/useLocalState";

interface AnalyticsCenterProps extends WorkspaceProps {}

const DEFAULT_FORM: AnalyticsRequest = {
  analytics_type: "executive_dashboard",
  brand: ANALYTICS_DEFAULTS.brand,
  platform: ANALYTICS_DEFAULTS.platform,
  date_range: { start: "", end: "" },
  filters: {
    campaign_type: "",
    content_type: "",
    workflow_type: "",
    asset_type: "",
  },
  include_storage: true,
  include_tokens: true,
  include_costs: true,
  include_governance: true,
  include_reports: true,
};

function toBreakdownRows(breakdown: Record<string, unknown> | undefined, valueKey: string): Array<{ label: string; value: string }> {
  if (!breakdown) {
    return [];
  }
  return Object.entries(breakdown)
    .slice(0, 8)
    .map(([label, value]) => ({
      label,
      value: String((value as Record<string, unknown> | undefined)?.[valueKey] ?? value ?? "-"),
    }));
}

export function AnalyticsCenter({ client, analyticsSummary, analyticsDashboard, analyticsHealth, activeBrand }: AnalyticsCenterProps) {
  const [form, setForm] = useLocalState<AnalyticsRequest>("amcs:analytics-form", DEFAULT_FORM);
  const [result, setResult] = useState<AnalyticsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const activeAnalytics = result ?? analyticsSummary ?? analyticsDashboard ?? null;
  const sections = (activeAnalytics?.sections ?? {}) as Record<string, unknown>;
  const kpis = (activeAnalytics?.kpis ?? {}) as Record<string, Record<string, { value?: number | string; label?: string; unit?: string; status?: string; description?: string }>>;
  const dashboard = (activeAnalytics?.dashboard_payload ?? analyticsDashboard ?? null) as any;
  const insights = activeAnalytics?.insights ?? dashboard?.summaries?.insights ?? [];
  const recommendations = activeAnalytics?.recommendations ?? dashboard?.summaries?.recommendations ?? [];
  const recentActivity = dashboard?.recent_activity ?? activeAnalytics?.trends?.recent_activity ?? [];
  const recordsCollected = Number((activeAnalytics?.metadata as any)?.records_collected ?? dashboard?.health?.records_count ?? 0);
  const hasAnalyticsData = recordsCollected > 0;

  useEffect(() => {
    if (activeBrand && activeBrand !== form.brand) {
      setForm((current) => ({ ...current, brand: activeBrand } as AnalyticsRequest));
    }
  }, [activeBrand, form.brand, setForm]);

  const flatExecutiveKpis = useMemo(() => Object.values(kpis.executive ?? {}), [kpis]);
  const flatOperationalKpis = useMemo(() => Object.values(kpis.operational ?? {}), [kpis]);

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    const response = await client.queryAnalytics(form);
    if (response.success && response.data) {
      setResult(response.data as AnalyticsResult);
    } else {
      setResult(null);
      setError(response.errors?.[0] ?? "Unable to query analytics.");
    }
    setLoading(false);
  };

  const updateFilter = (key: string, value: unknown) => {
    setForm((current) => ({
      ...current,
      [key]: value,
    } as AnalyticsRequest));
  };

  const updateNestedFilter = (key: string, value: string) => {
    setForm((current) => ({
      ...current,
      filters: {
        ...(current.filters ?? {}),
        [key]: value,
      },
    } as AnalyticsRequest));
  };

  const analyticsHealthLabel = String((analyticsHealth?.sections as any)?.health?.status ?? analyticsHealth?.status ?? "unknown");

  return (
    <div className="content-grid">
      <Card>
        <SectionHeader
          title="Analytics Center"
          description="Query executive, workflow, token, cost, and storage analytics from the backend."
          actions={<StatusPill status={analyticsHealthLabel} />}
        />
        <div className="form-grid">
          <div className="field">
            <label htmlFor="analytics_type">Analytics Type</label>
            <select id="analytics_type" className="select" value={form.analytics_type} onChange={(event) => updateFilter("analytics_type", event.target.value)}>
              {[
                "executive_dashboard",
                "workflow_analytics",
                "campaign_analytics",
                "generation_analytics",
                "asset_analytics",
                "token_analytics",
                "cost_analytics",
                "governance_analytics",
                "report_analytics",
                "storage_analytics",
                "api_health_analytics",
              ].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="brand">Brand</label>
            <input id="brand" className="input" value={form.brand ?? ""} onChange={(event) => updateFilter("brand", event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="platform">Platform</label>
            <input id="platform" className="input" value={form.platform ?? ""} onChange={(event) => updateFilter("platform", event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="start">Start Date</label>
            <input id="start" className="input" value={form.date_range?.start ?? ""} onChange={(event) => updateFilter("date_range", { ...(form.date_range ?? {}), start: event.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="end">End Date</label>
            <input id="end" className="input" value={form.date_range?.end ?? ""} onChange={(event) => updateFilter("date_range", { ...(form.date_range ?? {}), end: event.target.value })} />
          </div>
          <div className="field">
            <label htmlFor="campaign_type">Campaign Type</label>
            <input id="campaign_type" className="input" value={String(form.filters?.campaign_type ?? "")} onChange={(event) => updateNestedFilter("campaign_type", event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="content_type">Content Type</label>
            <input id="content_type" className="input" value={String(form.filters?.content_type ?? "")} onChange={(event) => updateNestedFilter("content_type", event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="workflow_type">Workflow Type</label>
            <input id="workflow_type" className="input" value={String(form.filters?.workflow_type ?? "")} onChange={(event) => updateNestedFilter("workflow_type", event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="asset_type">Asset Type</label>
            <input id="asset_type" className="input" value={String(form.filters?.asset_type ?? "")} onChange={(event) => updateNestedFilter("asset_type", event.target.value)} />
          </div>
          <div className="field field--full">
            <label htmlFor="reports">Include Reports</label>
            <div className="button-row">
              <Button type="button" variant={form.include_reports ? "primary" : "secondary"} onClick={() => updateFilter("include_reports", !form.include_reports)}>
                {form.include_reports ? "Enabled" : "Disabled"}
              </Button>
              <Button type="button" variant={form.include_storage ? "primary" : "secondary"} onClick={() => updateFilter("include_storage", !form.include_storage)}>
                Storage
              </Button>
              <Button type="button" variant={form.include_tokens ? "primary" : "secondary"} onClick={() => updateFilter("include_tokens", !form.include_tokens)}>
                Tokens
              </Button>
              <Button type="button" variant={form.include_costs ? "primary" : "secondary"} onClick={() => updateFilter("include_costs", !form.include_costs)}>
                Costs
              </Button>
              <Button type="button" variant={form.include_governance ? "primary" : "secondary"} onClick={() => updateFilter("include_governance", !form.include_governance)}>
                Governance
              </Button>
            </div>
          </div>
        </div>
        <div className="button-row" style={{ marginTop: 20 }}>
          <Button type="button" variant="primary" onClick={handleSubmit} disabled={loading}>
            {loading ? "Querying..." : "Query Analytics"}
          </Button>
        </div>
        {loading ? <LoadingState label="Loading analytics..." /> : null}
        {error ? <ErrorState message={error} /> : null}
        {analyticsHealth?.warnings?.length ? (
          <div className="section">
            <h3>Analytics Health</h3>
            <ul className="simple-list">
              {analyticsHealth.warnings?.map((warning, index) => (
                <li key={`${warning}-${index}`}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </Card>

      <Card className="panel--sticky">
        <SectionHeader title="Analytics Preview" description="KPI grid, breakdowns, insights, and safe JSON preview." />
        {activeAnalytics ? (
          <div className="result-panel">
            <StatusPill status={String(activeAnalytics.analytics_type ?? "analytics")} />
            {!hasAnalyticsData ? (
              <EmptyState
                title="No analytics data yet"
                description="Run a persisted workflow or generate content with reporting enabled to populate the analytics dashboard."
              />
            ) : null}
            <div className="metric-grid">
              {flatExecutiveKpis.slice(0, 4).map((item) => (
                <MetricCard
                  key={String(item.label ?? item.description ?? Math.random())}
                  label={String(item.label ?? "KPI")}
                  value={String(item.value ?? "-")}
                  hint={String(item.description ?? item.unit ?? "")}
                />
              ))}
            </div>
            {flatOperationalKpis.length > 0 ? (
              <div className="metric-grid">
                {flatOperationalKpis.slice(0, 4).map((item) => (
                  <MetricCard
                    key={String(item.label ?? item.description ?? Math.random())}
                    label={String(item.label ?? "KPI")}
                    value={String(item.value ?? "-")}
                    hint={String(item.description ?? item.unit ?? "")}
                  />
                ))}
              </div>
            ) : null}
            {dashboard?.cards?.length ? (
              <div className="section">
                <h3>Dashboard Cards</h3>
                <div className="metric-grid">
                  {dashboard.cards.slice(0, 4).map((card: Record<string, unknown>, index: number) => (
                    <MetricCard
                      key={`${String(card.label ?? "card")}-${index}`}
                      label={String(card.label ?? "Card")}
                      value={String(card.value ?? "-")}
                      hint={String(card.description ?? card.unit ?? "")}
                    />
                  ))}
                </div>
              </div>
            ) : null}
            <div className="grid-2">
              <Card>
                <SectionHeader title="Workflow Status" description="Latest workflow breakdown." />
                <table className="simple-table">
                  <tbody>
                    {toBreakdownRows((sections.workflows as Record<string, unknown>)?.status_breakdown as Record<string, unknown> | undefined, "value").map((row) => (
                      <tr key={row.label}>
                        <th>{row.label}</th>
                        <td>{row.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
              <Card>
                <SectionHeader title="Platform / Brand" description="Top grouping summaries." />
                <div className="section">
                  <strong>Platform</strong>
                  <table className="simple-table">
                    <tbody>
                      {toBreakdownRows((sections.platform_breakdown as Record<string, unknown>)?.groups as Record<string, unknown> | undefined, "value").map((row) => (
                        <tr key={row.label}>
                          <th>{row.label}</th>
                          <td>{row.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="section">
                  <strong>Brand</strong>
                  <table className="simple-table">
                    <tbody>
                      {toBreakdownRows((sections.brand_breakdown as Record<string, unknown>)?.groups as Record<string, unknown> | undefined, "value").map((row) => (
                        <tr key={row.label}>
                          <th>{row.label}</th>
                          <td>{row.value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
            <div className="grid-2">
              <Card>
                <SectionHeader title="Token / Cost" description="Tracked usage metrics." />
                <p><strong>Tokens:</strong> {formatCount((sections.tokens as Record<string, unknown>)?.total_tokens ?? 0)}</p>
                <p><strong>Estimated Token Records:</strong> {formatCount((sections.tokens as Record<string, unknown>)?.estimated_records ?? 0)}</p>
                <p><strong>Cost:</strong> {formatCurrency((sections.costs as Record<string, unknown>)?.total_cost ?? 0, String((sections.costs as Record<string, unknown>)?.currency ?? "USD"))}</p>
                <p><strong>Unknown Pricing:</strong> {formatCount((sections.costs as Record<string, unknown>)?.unknown_pricing_records ?? 0)}</p>
              </Card>
              <Card>
                <SectionHeader title="Insights" description="Rule-based observations and next actions." />
                {insights.length > 0 ? (
                  <ul className="simple-list">
                    {insights.slice(0, 4).map((item, index) => (
                      <li key={`${item}-${index}`}>{String(item)}</li>
                    ))}
                  </ul>
                ) : (
                  <EmptyState title="No insights yet" description="Run more persisted workflows to build richer analytics." />
                )}
                {recommendations.length > 0 ? (
                  <div className="section">
                    <h3>Recommendations</h3>
                    <ul className="simple-list">
                      {recommendations.slice(0, 4).map((item, index) => (
                        <li key={`${item}-${index}`}>{String(item)}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </Card>
            </div>
            {recentActivity.length > 0 ? (
              <Card>
                <SectionHeader title="Recent Activity" description="Latest normalized records." />
                <table className="simple-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Brand</th>
                      <th>Platform</th>
                      <th>Status</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentActivity.slice(0, 8).map((item: Record<string, unknown>, index: number) => (
                      <tr key={`${String(item.record_id ?? index)}`}>
                        <td>{String(item.record_type ?? "-")}</td>
                        <td>{String(item.brand ?? "-")}</td>
                        <td>{String(item.platform ?? "-")}</td>
                        <td>{String(item.status ?? "-")}</td>
                        <td>{String(item.created_at ?? "-")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            ) : null}
            <JsonViewer data={activeAnalytics} title="Safe Analytics JSON" />
          </div>
        ) : (
          <EmptyState
            title="No analytics yet"
            description="Run generation or workflow requests to populate the executive dashboard."
            action={(
              <Button type="button" variant="secondary" onClick={() => setForm(DEFAULT_FORM)}>
                Reset Filters
              </Button>
            )}
          />
        )}
      </Card>
    </div>
  );
}
