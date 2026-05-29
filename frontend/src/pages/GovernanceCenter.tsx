import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { JsonViewer } from "../components/JsonViewer";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { StatusPill } from "../components/StatusPill";
import type { WorkspaceProps } from "./shared";
import { getSnapshotChain } from "./shared";

interface GovernanceCenterProps extends WorkspaceProps {}

export function GovernanceCenter({ snapshots }: GovernanceCenterProps) {
  const source = getSnapshotChain<any>(snapshots, ["workflow", "generate", "campaign", "assets"]);
  const governance = (source?.governance_result ?? source?.governance_summary ?? source?.validation_result ?? null) as any;

  if (!governance) {
    return (
      <Card>
        <SectionHeader title="Governance Center" description="Approval, compliance, and safety signals from the latest system activity." />
        <EmptyState title="No governance data yet" description="Run generation or a workflow to surface governance summaries here." />
      </Card>
    );
  }

  return (
    <div className="stack">
      <SectionHeader title="Governance Center" description="Approval status, safety notes, and compliance signals." />
      <div className="metric-grid">
        <MetricCard label="Approval" value={String(governance.approved ?? governance.approval_status ?? "-")} hint={String(governance.status ?? "status")} />
        <MetricCard label="Overall Score" value={String(governance.overall_score ?? governance.quality_score ?? "-")} hint="Quality" />
        <MetricCard label="Brand Score" value={String(governance.brand_score ?? "-")} hint="Brand fit" />
        <MetricCard label="Platform Score" value={String(governance.platform_score ?? "-")} hint="Platform fit" />
      </div>
      <Card>
        <SectionHeader title="Governance Details" description="Warnings, errors, and recommendations." />
        <StatusPill status={String(governance.status ?? "review")} />
        <JsonViewer data={governance} title="Governance JSON" />
      </Card>
    </div>
  );
}
