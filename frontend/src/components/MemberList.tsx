import type { MembershipProfile } from "../types/api";
import { EmptyState } from "./EmptyState";
import { Card } from "./Card";
import { SectionHeader } from "./SectionHeader";
import { Badge } from "./Badge";

interface MemberListProps {
  members: MembershipProfile[];
}

export function MemberList({ members }: MemberListProps) {
  return (
    <Card>
      <SectionHeader title="Members" description="Organization membership overview." />
      {members.length ? (
        <div className="stack">
          {members.map((member) => (
            <div className="metric-card" key={String(member.membership_id ?? member.user_id)}>
              <div className="row-between">
                <strong>{String(member.user_id ?? "-")}</strong>
                <Badge tone={member.status === "inactive" ? "warning" : "success"}>{String(member.role ?? "member")}</Badge>
              </div>
              <p className="muted">{String(member.team_id ?? "Organization-wide")}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No members" description="Add members to start collaborating inside this organization." />
      )}
    </Card>
  );
}
