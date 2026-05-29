import { ConfigurationCard } from "./ConfigurationCard";
import { EmptyState } from "./EmptyState";
import { MetricCard } from "./MetricCard";
import { StatusPill } from "./StatusPill";

interface SecurityStatusCardProps {
  securityStatus?: Record<string, unknown> | null;
  securityHealth?: Record<string, unknown> | null;
  securityFindings?: Record<string, unknown> | null;
  securityDependencies?: Record<string, unknown> | null;
  securityConfiguration?: Record<string, unknown> | null;
}

export function SecurityStatusCard({ securityStatus, securityHealth, securityFindings, securityDependencies, securityConfiguration }: SecurityStatusCardProps) {
  const score = Number(securityHealth?.security_score ?? securityStatus?.security_score ?? 0);
  const status = String(securityHealth?.security_status ?? securityStatus?.security_status ?? "unknown");
  const baselineReady = Boolean(securityHealth?.baseline_ready ?? securityStatus?.baseline_ready ?? false);
  const baselineScore = Number(securityHealth?.baseline_score ?? securityStatus?.baseline_score ?? 0);
  const baselineStatus = String(securityHealth?.baseline_status ?? securityStatus?.baseline_status ?? "unknown");
  const protections = securityStatus?.active_protections ? Object.values(securityStatus.active_protections as Record<string, boolean>).filter(Boolean).length : 0;
  const findingsCount = Number(securityStatus?.findings_count ?? securityFindings?.count ?? (Array.isArray(securityStatus?.findings) ? securityStatus?.findings?.length : 0));
  const healthDependencies = (securityHealth?.dependencies as Record<string, unknown> | undefined) ?? {};
  const dependenciesValid = Boolean(securityDependencies?.dependencies_valid ?? healthDependencies.dependencies_valid ?? true);
  const recentWarnings = Array.isArray(securityHealth?.recent_security_warnings) ? securityHealth.recent_security_warnings : [];

  return (
    <ConfigurationCard title="Security Hardening" description="Final MVP release security posture and active protections.">
      {securityStatus || securityHealth ? (
        <div className="row">
          <StatusPill status={status} />
        </div>
      ) : null}
      {securityStatus || securityHealth ? (
        <div className="metric-grid">
          <MetricCard label="Security Score" value={String(score)} hint="0-100" />
          <MetricCard label="Status" value={status} hint="Current posture" />
          <MetricCard label="Baseline" value={baselineReady ? "Ready" : "Review"} hint={`${baselineScore}% ${baselineStatus}`} />
          <MetricCard label="Active Protections" value={String(protections)} hint="Enabled guards" />
          <MetricCard label="Findings" value={String(findingsCount)} hint={dependenciesValid ? "Dependencies valid" : "Review dependencies"} />
        </div>
      ) : (
        <EmptyState title="Security data unavailable" description="Authenticate to view security hardening status." />
      )}
      <div className="grid-2">
        <ConfigurationCard title="Protections" description="Active hardening controls.">
          <ul className="simple-list">
            {Object.entries((securityStatus?.active_protections as Record<string, boolean>) ?? (securityConfiguration?.active_protections as Record<string, boolean>) ?? {}).map(([key, enabled]) => (
              <li key={key}>
                {key}: {enabled ? "Enabled" : "Disabled"}
              </li>
            ))}
          </ul>
        </ConfigurationCard>
        <ConfigurationCard title="Release Readiness" description="Security readiness metadata for MVP release.">
          <div className="metric-grid">
            <MetricCard label="Dependencies" value={dependenciesValid ? "Valid" : "Needs review"} hint="Package safety" />
            <MetricCard label="Release Ready" value={String(Boolean(securityHealth?.release_ready ?? securityStatus?.release_ready ?? false))} hint="MVP readiness" />
            <MetricCard label="Security Ready" value={String(Boolean(securityHealth?.security_ready ?? securityStatus?.security_ready ?? false))} hint="Security readiness" />
            <MetricCard label="Configuration" value={String(Boolean(securityConfiguration?.security_enabled ?? true))} hint="Active config" />
          </div>
          {recentWarnings.length ? (
            <div className="section">
              <h3>Recent Security Warnings</h3>
              <ul className="simple-list">
                {recentWarnings.slice(0, 3).map((warning: string, index: number) => (
                  <li key={`${warning}-${index}`}>{warning}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </ConfigurationCard>
      </div>
    </ConfigurationCard>
  );
}
