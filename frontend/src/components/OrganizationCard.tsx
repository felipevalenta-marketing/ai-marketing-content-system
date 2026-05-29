import type { OrganizationProfile } from "../types/api";
import { Card } from "./Card";
import { MetricCard } from "./MetricCard";
import { SectionHeader } from "./SectionHeader";

interface OrganizationCardProps {
  organization: OrganizationProfile | null;
}

export function OrganizationCard({ organization }: OrganizationCardProps) {
  if (!organization) {
    return null;
  }

  return (
    <Card>
      <SectionHeader title="Organization" description="Selected organization profile and access summary." />
      <div className="metric-grid">
        <MetricCard label="Name" value={String(organization.name ?? organization.organization_id ?? "-")} hint={String(organization.slug ?? "")} />
        <MetricCard label="Status" value={String(organization.status ?? "active")} hint={String(organization.owner_user_id ?? "owner")} />
        <MetricCard label="Health" value={String(organization.health_score ?? "-")} hint={String(organization.health_status ?? "health")} />
        <MetricCard label="Teams" value={String(organization.team_count ?? 0)} hint="Accessible teams" />
        <MetricCard label="Members" value={String(organization.member_count ?? 0)} hint="Organization members" />
      </div>
    </Card>
  );
}
