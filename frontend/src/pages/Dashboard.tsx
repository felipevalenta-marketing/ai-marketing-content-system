import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { extractMarkdown, formatCount, formatCurrency, formatPercent, getStatusLabel } from "../utils/formatting";
import type { WorkspaceProps } from "./shared";
import { getSnapshot } from "./shared";
import type { AnalyticsDashboardData, AnalyticsHealthData, AnalyticsSummaryData } from "../types/api";

interface DashboardProps extends WorkspaceProps {
  onNavigate: (page: string) => void;
  onCheckHealth: () => void;
}

function readTokenSummary(snapshots: WorkspaceProps["snapshots"]) {
  const workflow = getSnapshot<any>(snapshots, "workflow");
  const generate = getSnapshot<any>(snapshots, "generate");
  const source = workflow ?? generate ?? null;
  return (source && (source.token_summary || source.token_usage || source.execution_token_summary)) as any;
}

function readCostSummary(snapshots: WorkspaceProps["snapshots"]) {
  const workflow = getSnapshot<any>(snapshots, "workflow");
  const generate = getSnapshot<any>(snapshots, "generate");
  const source = workflow ?? generate ?? null;
  return (source && (source.cost_summary || source.cost_usage || source.execution_cost_summary)) as any;
}

export function Dashboard({ snapshots, health, config, analyticsSummary, analyticsDashboard, analyticsHealth, activeBrand, brandProfile, brandValidation, brandDefaults, brands, permissions = [], onNavigate, onCheckHealth }: DashboardProps) {
  const workflow = getSnapshot<any>(snapshots, "workflow");
  const generate = getSnapshot<any>(snapshots, "generate");
  const reports = getSnapshot<any>(snapshots, "reports");
  const storage = getSnapshot<any>(snapshots, "storage");
  const tokenSummary = readTokenSummary(snapshots);
  const costSummary = readCostSummary(snapshots);
  const latestMarkdown = extractMarkdown(reports) || extractMarkdown(workflow) || extractMarkdown(generate);
  const modules = config?.feature_flags ? Object.values(config.feature_flags).filter(Boolean).length : 0;
  const analyticsSummaryData = analyticsSummary as AnalyticsSummaryData | null;
  const analyticsDashboardData = analyticsDashboard as AnalyticsDashboardData | null;
  const analyticsHealthData = analyticsHealth as AnalyticsHealthData | null;
  const dashboardPayload = analyticsDashboardData ?? analyticsSummaryData?.dashboard_payload ?? null;
  const dashboardCards = Array.isArray(dashboardPayload?.cards) ? dashboardPayload.cards : [];
  const dashboardHealth = (analyticsHealthData?.sections as any)?.health ?? dashboardPayload?.health ?? (analyticsSummaryData?.sections as any)?.storage ?? null;
  const executiveSummary = analyticsSummaryData?.executive_summary ?? dashboardPayload?.summaries?.executive ?? null;
  const recentActivity = dashboardPayload?.recent_activity ?? (analyticsSummaryData?.trends as any)?.recent_activity ?? [];
  const analyticsInsights = analyticsSummaryData?.insights ?? dashboardPayload?.summaries?.insights ?? [];
  const analyticsRecommendations = analyticsSummaryData?.recommendations ?? dashboardPayload?.summaries?.recommendations ?? [];
  const executiveKpis = (analyticsSummaryData?.kpis as any)?.executive ?? {};
  const hasAnalytics = Boolean(analyticsSummaryData || analyticsDashboardData || dashboardPayload);
  const analyticsRecords = Number((analyticsSummaryData?.metadata as any)?.records_collected ?? dashboardHealth?.records_count ?? 0);
  const analyticsIsEmpty = hasAnalytics && analyticsRecords <= 0;
  const brandValidationData = brandValidation as any;
  const can = (permission: string) => permissions.includes("admin:all") || permissions.includes(permission);

  return (
    <div className="stack">
      <SectionHeader
        title="Dashboard"
        description="A compact operating view of the system, with live API status and recent workspace activity."
      />

      <div className="metric-grid">
        <MetricCard label="API Status" value={getStatusLabel(health?.status ?? "unknown")} hint={health?.service ?? "service"} />
        <MetricCard label="Environment" value={config?.app_env ?? "development"} hint={config?.default_model ?? "model"} />
        <MetricCard label="Enabled Modules" value={formatCount(modules)} hint="Feature flags" />
        <MetricCard label="Storage Root" value={config?.storage_root ?? "data"} hint="Local persistence" />
      </div>

      <Card>
        <SectionHeader title="Brand Management" description="Selected brand, validation status, and safe defaults." />
        <div className="grid-2">
          <MetricCard label="Active Brand" value={String(activeBrand ?? config?.default_brand ?? "-")} hint={String(brandProfile?.display_name ?? "Selected")} />
          <MetricCard label="Brand Status" value={String(brandProfile?.status ?? brandValidationData?.valid ?? "unknown")} hint={String(brandProfile?.knowledge_path ?? "profile")} />
        </div>
        <div className="metric-grid">
          <MetricCard label="Health Score" value={String(brandProfile?.health_score ?? "-")} hint={String(brandProfile?.health_status ?? "health")} />
          <MetricCard label="Markdown Files" value={String(brandProfile?.metadata?.markdown_count ?? 0)} hint="Readable files" />
        </div>
        <div className="grid-2">
          <div className="section">
            <h3>Defaults</h3>
            <ul className="simple-list">
              <li>Platform: {String(brandDefaults?.default_platform ?? config?.default_platform ?? "instagram")}</li>
              <li>Content Type: {String(brandDefaults?.default_content_type ?? config?.default_content_type ?? "instagram_post")}</li>
              <li>Campaign Type: {String(brandDefaults?.default_campaign_type ?? config?.default_campaign_type ?? "property_launch")}</li>
            </ul>
          </div>
          <div className="section">
            <h3>Brands</h3>
            {brands?.length ? (
              <ul className="simple-list">
                {brands.slice(0, 5).map((brand) => (
                  <li key={String(brand.brand_id ?? brand.display_name)}>
                    {String(brand.display_name ?? brand.brand_id)}
                    {typeof brand.health_score === "number" ? ` · ${brand.health_score}/100` : ""}
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No brands found" description="Create a brand folder under brands/ to start." />
            )}
          </div>
        </div>
        {Array.isArray(brandValidationData?.warnings) && brandValidationData.warnings.length ? (
          <div className="section">
            <h3>Validation Warnings</h3>
            <ul className="simple-list">
              {brandValidationData.warnings.slice(0, 3).map((warning: string, index: number) => (
                <li key={`${warning}-${index}`}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </Card>

      {hasAnalytics ? (
        <Card>
          <SectionHeader title="Executive Analytics" description="Live dashboard-ready summaries from the backend analytics layer." />
          {analyticsIsEmpty ? (
            <EmptyState
              title="No analytics data yet"
              description="Run a persisted workflow or generate content with reporting enabled to populate executive KPIs, recent activity, and cost summaries."
              action={
                <>
                  <Button type="button" variant="primary" onClick={() => onNavigate("workflow")}>
                    Run Workflow Dry Run
                  </Button>
                  <Button type="button" variant="secondary" onClick={() => onNavigate("content")}>
                    Generate Content
                  </Button>
                  <Button type="button" variant="secondary" onClick={onCheckHealth}>
                    Check API Health
                  </Button>
                  <Button type="button" variant="secondary" onClick={() => onNavigate("storage")}>
                    Browse Storage
                  </Button>
                </>
              }
            />
          ) : executiveSummary ? (
            <div className="section">
              <StatusPill status={String(executiveSummary.approval_status ?? dashboardHealth?.status ?? "neutral")} />
              <p><strong>{String(executiveSummary.headline ?? "Analytics ready")}</strong></p>
              <p>{String(executiveSummary.outcome ?? "")}</p>
            </div>
          ) : null}
          <div className="metric-grid">
            {dashboardCards.length > 0
              ? dashboardCards.slice(0, 4).map((card, index) => (
                  <MetricCard
                    key={`${String(card.label ?? "card")}-${index}`}
                    label={String(card.label ?? "Metric")}
                    value={String(card.value ?? "-")}
                    hint={card.description ? String(card.description) : String(card.unit ?? "")}
                  />
                ))
              : (
                <>
                  <MetricCard label="Total Tokens" value={formatCount(Number(executiveKpis.total_tokens?.value ?? 0))} hint="Analytics" />
                  <MetricCard label="Total Cost" value={formatCurrency(Number(executiveKpis.total_cost?.value ?? 0), String((costSummary as any)?.currency ?? "USD"))} hint="Analytics" />
                  <MetricCard label="Workflow Success" value={formatPercent(Number(executiveKpis.workflow_success_rate?.value ?? 0))} hint="Analytics" />
                  <MetricCard label="Approval Rate" value={formatPercent(Number(executiveKpis.governance_approval_rate?.value ?? 0))} hint="Analytics" />
                </>
              )}
          </div>
          {recentActivity.length > 0 ? (
            <div className="section">
              <h3>Recent Activity</h3>
              <div className="stack">
                {recentActivity.slice(0, 4).map((item, index) => (
                  <div key={`${String(item.record_id ?? index)}`} className="metric-card">
                    <p className="metric-card__label">{String(item.record_type ?? "record")}</p>
                    <p className="metric-card__value">{String(item.brand ?? item.platform ?? "Activity")}</p>
                    <p className="metric-card__hint">{String(item.created_at ?? item.status ?? "")}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {analyticsInsights.length > 0 ? (
            <div className="section">
              <h3>Insights</h3>
              <ul className="simple-list">
                {analyticsInsights.slice(0, 3).map((item, index) => (
                  <li key={`${String(item)}-${index}`}>{String(item)}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {analyticsRecommendations.length > 0 ? (
            <div className="section">
              <h3>Recommendations</h3>
              <ul className="simple-list">
                {analyticsRecommendations.slice(0, 3).map((item, index) => (
                  <li key={`${String(item)}-${index}`}>{String(item)}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </Card>
      ) : null}

      <div className="grid-2">
        <Card>
          <SectionHeader title="Latest Activity" description="Recent workflow, generation, report, and storage snapshots." />
          {workflow || generate || reports || storage ? (
            <div className="section">
              {workflow ? <StatusPill status={String(workflow.status ?? "running")} /> : null}
              {generate ? <p><strong>Generation:</strong> {getStatusLabel(String(generate.success ? "success" : "warning"))}</p> : null}
              {reports ? <p><strong>Reports:</strong> Available</p> : null}
              {storage ? <p><strong>Storage:</strong> Records available</p> : null}
            </div>
          ) : (
            <EmptyState
              title="No recent activity yet"
              description="Run content generation or a workflow to populate the dashboard with live summaries."
              action={
                <>
                  <Button type="button" variant="primary" onClick={() => onNavigate("content")}>
                    Generate Content
                  </Button>
                  <Button type="button" variant="secondary" onClick={() => onNavigate("workflow")}>
                    Run Workflow Dry Run
                  </Button>
                  <Button type="button" variant="secondary" onClick={onCheckHealth}>
                    Check API Health
                  </Button>
                  <Button type="button" variant="secondary" onClick={() => onNavigate("storage")}>
                    Browse Storage
                  </Button>
                </>
              }
            />
          )}
        </Card>

        <Card>
          <SectionHeader title="Quick Actions" description="Move quickly between common workflows." />
          <div className="grid-2">
            {can("generation:create") ? <Button type="button" variant="primary" onClick={() => onNavigate("content")}>Generate Content</Button> : null}
            {can("workflow:run") ? <Button type="button" variant="secondary" onClick={() => onNavigate("workflow")}>Run Workflow</Button> : null}
            {can("report:read") ? <Button type="button" variant="secondary" onClick={() => onNavigate("reports")}>View Reports</Button> : null}
            {can("storage:read") ? <Button type="button" variant="secondary" onClick={() => onNavigate("storage")}>Browse Storage</Button> : null}
          </div>
        </Card>
      </div>

      <div className="metric-grid">
        <MetricCard
          label="Input Tokens"
          value={formatCount(tokenSummary?.input_tokens ?? tokenSummary?.total_input_tokens ?? 0)}
          hint={String(tokenSummary?.provider ?? "provider")}
        />
        <MetricCard
          label="Output Tokens"
          value={formatCount(tokenSummary?.output_tokens ?? tokenSummary?.total_output_tokens ?? 0)}
          hint={String(tokenSummary?.model ?? "model")}
        />
        <MetricCard
          label="Total Cost"
          value={formatCurrency(costSummary?.total_cost ?? 0, String(costSummary?.currency ?? "USD"))}
          hint={costSummary?.estimated_cost ? "Estimated" : "Known pricing"}
        />
        <MetricCard
          label="Storage Records"
          value={formatCount(storage?.count ?? (storage?.records as unknown[] | undefined)?.length ?? 0)}
          hint="Available records"
        />
      </div>

      {latestMarkdown ? (
        <Card>
          <SectionHeader title="Latest Markdown" description="The most recent markdown report preview from the workspace." />
          <pre className="code-block">{latestMarkdown}</pre>
        </Card>
      ) : null}
    </div>
  );
}
