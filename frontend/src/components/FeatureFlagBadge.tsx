import { Badge } from "./Badge";

interface FeatureFlagBadgeProps {
  label: string;
  enabled?: boolean;
}

export function FeatureFlagBadge({ label, enabled = false }: FeatureFlagBadgeProps) {
  return <Badge tone={enabled ? "success" : "warning"}>{`${label}: ${enabled ? "Enabled" : "Disabled"}`}</Badge>;
}

