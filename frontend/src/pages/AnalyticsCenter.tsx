import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { JsonViewer } from "../components/JsonViewer";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { extractMarkdown, formatCount, formatCurrency } from "../utils/formatting";
import type { WorkspaceProps } from "./shared";
import { getSnapshot, getSnapshotChain } from "./shared";

interface AnalyticsCenterProps extends WorkspaceProps {}

export function AnalyticsCenter({ snapshots }: AnalyticsCenterProps) {
  const workflow = getSnapshot<any>(snapshots, "workflow");
  const generate = getSnapshot<any>(snapshots, "generate");
  const tokenSummary = (workflow?.token_summary ?? generate?.token_summary ?? generate?.token_usage ?? null) as any;
  const costSummary = (workflow?.cost_summary ?? generate?.cost_summary ?? generate?.cost_usage ?? null) as any;
  const reportSummary = getSnapshotChain<any>(snapshots, ["reports", "workflow", "generate"]);
  const markdown = extractMarkdown(reportSummary) || extractMarkdown(workflow) || extractMarkdown(generate);

  if (!tokenSummary && !costSummary && !reportSummary) {
    return (
      <Card>
        <SectionHeader title="Analytics Center" description="Token, cost, and reporting metrics appear after running generation or workflows." />
        <EmptyState title="No analytics yet" description="Run a generation or workflow to populate token and cost summaries." />
      </Card>
    );
  }

  return (
    <div className="stack">
      <SectionHeader title="Analytics Center" description="A compact summary of usage, spend, and reporting outputs." />
      <div className="metric-grid">
        <MetricCard label="Input Tokens" value={formatCount(tokenSummary?.input_tokens ?? 0)} hint={String(tokenSummary?.provider ?? "provider")} />
        <MetricCard label="Output Tokens" value={formatCount(tokenSummary?.output_tokens ?? 0)} hint={String(tokenSummary?.model ?? "model")} />
        <MetricCard label="Total Cost" value={formatCurrency(costSummary?.total_cost ?? 0, String(costSummary?.currency ?? "USD"))} hint={costSummary?.estimated_cost ? "Estimated" : "Known"} />
        <MetricCard label="Workflow Status" value={String(workflow?.status ?? generate?.status ?? "-")} hint="Latest workflow/generation" />
      </div>
      <Card>
        <SectionHeader title="Breakdowns" description="Provider, model, and module summaries when available." />
        <JsonViewer data={{ tokenSummary, costSummary, reportSummary }} title="Analytics JSON" />
        {markdown ? <pre className="code-block">{markdown}</pre> : null}
      </Card>
    </div>
  );
}
