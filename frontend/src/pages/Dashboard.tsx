import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import { extractMarkdown, formatCount, formatCurrency, getStatusLabel } from "../utils/formatting";
import type { WorkspaceProps } from "./shared";
import { getSnapshot } from "./shared";

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

export function Dashboard({ snapshots, health, config, onNavigate, onCheckHealth }: DashboardProps) {
  const workflow = getSnapshot<any>(snapshots, "workflow");
  const generate = getSnapshot<any>(snapshots, "generate");
  const reports = getSnapshot<any>(snapshots, "reports");
  const storage = getSnapshot<any>(snapshots, "storage");
  const tokenSummary = readTokenSummary(snapshots);
  const costSummary = readCostSummary(snapshots);
  const latestMarkdown = extractMarkdown(reports) || extractMarkdown(workflow) || extractMarkdown(generate);
  const modules = config?.feature_flags ? Object.values(config.feature_flags).filter(Boolean).length : 0;

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
            <Button type="button" variant="primary" onClick={() => onNavigate("content")}>
              Generate Content
            </Button>
            <Button type="button" variant="secondary" onClick={() => onNavigate("workflow")}>
              Run Workflow
            </Button>
            <Button type="button" variant="secondary" onClick={() => onNavigate("reports")}>
              View Reports
            </Button>
            <Button type="button" variant="secondary" onClick={() => onNavigate("storage")}>
              Browse Storage
            </Button>
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
