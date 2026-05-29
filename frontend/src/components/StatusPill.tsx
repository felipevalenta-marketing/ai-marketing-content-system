import { formatStatusTone, getStatusLabel } from "../utils/formatting";

interface StatusPillProps {
  status?: string;
}

export function StatusPill({ status }: StatusPillProps) {
  const tone = formatStatusTone(status);
  return <span className={`status-pill status-pill--${tone}`}>{getStatusLabel(status)}</span>;
}
