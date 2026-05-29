import { ConfigurationCard } from "./ConfigurationCard";
import { EmptyState } from "./EmptyState";
import { MetricCard } from "./MetricCard";
import { StatusPill } from "./StatusPill";
import type { ReleaseArtifactIndexData, ReleaseChecklistData, ReleaseCertificationData, ReleaseGovernanceData, ReleaseHealthData, ReleaseMaturityData, ReleaseReadinessData, ReleaseReportData, ReleaseScoreData, ReleaseStatusData } from "../types/api";

interface ReleaseStatusCardProps {
  releaseStatus?: ReleaseStatusData | null;
  releaseCertification?: ReleaseCertificationData | null;
  releaseMaturity?: ReleaseMaturityData | null;
  releaseGovernance?: ReleaseGovernanceData | null;
  releaseReadiness?: ReleaseReadinessData | null;
  releaseHealth?: ReleaseHealthData | null;
  releaseChecklist?: ReleaseChecklistData | null;
  releaseReport?: ReleaseReportData | null;
  releaseArtifacts?: ReleaseArtifactIndexData | null;
  releaseScore?: ReleaseScoreData | null;
}

export function ReleaseStatusCard({ releaseStatus, releaseCertification, releaseMaturity, releaseGovernance, releaseReadiness, releaseHealth, releaseChecklist, releaseReport, releaseArtifacts, releaseScore }: ReleaseStatusCardProps) {
  const status = String(releaseCertification?.certification_status ?? releaseStatus?.certification_status ?? releaseStatus?.release_status ?? releaseGovernance?.governance_status ?? releaseReadiness?.status ?? releaseScore?.release_status ?? releaseHealth?.overall_health ?? "blocked");
  const score = Number(releaseStatus?.release_score ?? releaseScore?.release_score ?? releaseStatus?.overall_score ?? releaseReadiness?.acceptance_score ?? releaseHealth?.health_score ?? releaseCertification?.release_score ?? 0);
  const checklist = releaseChecklist ?? (releaseStatus?.release_checklist as ReleaseChecklistData | undefined) ?? null;
  const reportReady = Boolean(releaseReport?.generated ?? releaseStatus?.mvp_acceptance);
  const certificationStatus = String(releaseCertification?.certification_status ?? releaseStatus?.certification_status ?? "blocked");
  const maturityLevel = String(releaseMaturity?.maturity_level ?? releaseStatus?.maturity_level ?? "prototype");
  const maturityScore = Number(releaseMaturity?.maturity_score ?? releaseStatus?.maturity_score ?? 0);
  const mvpCertified = Boolean(releaseCertification?.mvp_certified ?? releaseStatus?.mvp_ready ?? false);
  const productionReady = Boolean(releaseCertification?.production_ready ?? releaseStatus?.production_ready ?? false);

  if (!releaseStatus && !releaseReadiness && !releaseHealth && !releaseChecklist && !releaseReport && !releaseScore) {
    return (
      <ConfigurationCard title="Release Readiness" description="MVP acceptance, validation, and release certification.">
        <EmptyState title="Release data unavailable" description="Run the release readiness checks to populate the MVP acceptance summary." />
      </ConfigurationCard>
    );
  }

  return (
    <ConfigurationCard title="Release Readiness" description="MVP acceptance, validation, and release certification.">
      <div className="metric-grid">
        <MetricCard label="MVP Certified" value={String(mvpCertified)} hint="Final approval" />
        <MetricCard label="Production Ready" value={String(productionReady)} hint="Release gate" />
        <MetricCard label="Release Score" value={String(score)} hint="0-100" />
        <MetricCard label="Maturity Level" value={maturityLevel} hint={String(maturityScore)} />
        <MetricCard label="Certification Status" value={certificationStatus} hint={status} />
      </div>
      <div className="metric-grid">
        <MetricCard label="MVP Ready" value={String(Boolean(releaseReadiness?.mvp_ready ?? releaseStatus?.mvp_ready ?? false))} hint="Acceptance" />
        <MetricCard label="Security Ready" value={String(Boolean(releaseStatus?.security_ready ?? releaseReadiness?.validation?.security_ready ?? false))} hint="FR-038" />
        <MetricCard label="Deployment Ready" value={String(Boolean(releaseStatus?.deployment_ready ?? releaseReadiness?.validation?.deployment_ready ?? false))} hint="FR-035" />
        <MetricCard label="Observability Ready" value={String(Boolean(releaseStatus?.observability_ready ?? releaseHealth?.overall_health === "healthy"))} hint="FR-036" />
        <MetricCard label="CI Ready" value={String(Boolean(releaseStatus?.ci_ready ?? releaseReadiness?.validation?.ci_ready ?? false))} hint="FR-037" />
      </div>
      <div className="section">
        <StatusPill status={status} />
      </div>
      <div className="metric-grid">
        <MetricCard label="Checklist Complete" value={String(Number(checklist?.passed ?? checklist?.completed ?? 0))} hint={String(Number(checklist?.total_checks ?? checklist?.total ?? 0))} />
        <MetricCard label="Checklist Pending" value={String(Number(checklist?.failed ?? checklist?.pending ?? 0))} hint="Items left" />
        <MetricCard label="Report Ready" value={String(reportReady)} hint={releaseReport?.path ?? "docs/MVP_READINESS_REPORT.md"} />
        <MetricCard label="Health Score" value={String(Number(releaseHealth?.health_score ?? 0))} hint={String(releaseHealth?.overall_health ?? "critical")} />
      </div>
      <div className="metric-grid">
        <MetricCard label="Governance" value={String(releaseGovernance?.governance_status ?? releaseStatus?.readiness_status ?? "approved")} hint={String(releaseGovernance?.release_blocked ? "blocked" : "reviewed")} />
        <MetricCard label="Artifact Index" value={String(Boolean(releaseArtifacts?.generated ?? releaseStatus?.release_artifacts))} hint={releaseArtifacts?.path ?? "docs/RELEASE_ARTIFACTS.md"} />
      </div>
      {Array.isArray(releaseStatus?.warnings) && releaseStatus.warnings.length ? (
        <div className="section">
          <h3>Release Warnings</h3>
          <ul className="simple-list">
            {releaseStatus.warnings.slice(0, 3).map((warning, index) => (
              <li key={`${warning}-${index}`}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </ConfigurationCard>
  );
}
