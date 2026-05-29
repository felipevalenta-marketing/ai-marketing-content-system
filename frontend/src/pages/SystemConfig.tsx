import { useEffect, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { JsonViewer } from "../components/JsonViewer";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { getRoleLabel, getRoleTone } from "../utils/formatting";
import { ConfigurationCard } from "../components/ConfigurationCard";
import { FeatureFlagBadge } from "../components/FeatureFlagBadge";
import { OrganizationCard } from "../components/OrganizationCard";
import { SecurityStatusCard } from "../components/SecurityStatusCard";
import type { WorkspaceProps } from "./shared";

interface SystemConfigProps extends WorkspaceProps {}

export function SystemConfig({ client, config, observabilityHealth, observabilityStatus, observabilityDomains, observabilityTokens, observabilityCosts, observabilityConfiguration, observabilityMetrics, runtimeDiagnostics, recentErrors, workflowObservability, storageObservability, securityStatus, securityHealth, securityFindings, securityDependencies, securityConfiguration, activeBrand, activeOrganizationId, activeTeamId, brandProfile, brandValidation, brandDefaults, brands, organizations, organizationProfile, organizationMembers, role }: SystemConfigProps) {
  const canManageConfig = Boolean(role === "admin" || role === "manager");
  const [editableFlags, setEditableFlags] = useState<Record<string, boolean>>({});
  const [updateMessage, setUpdateMessage] = useState<string>("");

  useEffect(() => {
    setEditableFlags((config?.feature_flags ?? flagsFromConfig(config)) as Record<string, boolean>);
  }, [config]);

  if (!config) {
    return (
      <ConfigurationCard title="System Config" description="Safe runtime configuration and feature flags.">
        <EmptyState title="Config unavailable" description="Refresh the configuration to inspect safe runtime settings." />
      </ConfigurationCard>
    );
  }

  const summary = (config.configuration ?? config) as any;
  const platform = summary.platform_config ?? config.platform_config ?? config;
  const flags = summary.feature_flags ?? config.feature_flags ?? {};
  const modules = Array.isArray(summary.modules) ? summary.modules : Array.isArray(config.modules) ? config.modules : [];
  const limits = summary.limits ?? config.limits ?? {};
  const environment = summary.environment ?? config.environment ?? {};
  const health = summary.configuration_health ?? config.configuration_health ?? {};
  const observabilityHealthStatus = String(observabilityHealth?.status ?? "unknown");
  const observabilityMetricsData = observabilityMetrics ?? {};
  const runtime = runtimeDiagnostics ?? {};
  const recentErrorItems = Array.isArray(recentErrors?.recent_errors) ? recentErrors.recent_errors : [];
  const workflowSummary = workflowObservability ?? {};
  const storageSummary = storageObservability ?? {};
  const observabilityDomainItems = observabilityDomains?.domains ?? [];
  const observabilityTokensData = observabilityTokens?.metrics ?? {};
  const observabilityCostsData = observabilityCosts?.metrics ?? {};
  const observabilityConfigData = observabilityConfiguration ?? {};
  const brandValidationData = brandValidation as any;

  function flagsFromConfig(payload: typeof config | null): Record<string, boolean> {
    return (payload?.feature_flags ?? {}) as Record<string, boolean>;
  }

  const handleToggleFlag = async (flag: string, nextValue: boolean) => {
    const response = await client.updateFeatureFlag(flag, nextValue);
    if (response.success) {
      setEditableFlags((current) => ({
        ...current,
        [flag]: nextValue,
      }));
      setUpdateMessage(`Updated ${flag} to ${nextValue ? "enabled" : "disabled"}.`);
    } else {
      setUpdateMessage(response.errors?.[0] ?? "Unable to update feature flag.");
    }
  };

  return (
    <div className="stack">
      <SectionHeader title="System Config" description="Safe runtime configuration summary with secrets removed." />
      <div className="row">
        <Badge tone={getRoleTone(role)}>{getRoleLabel(role)}</Badge>
        <span className="muted">Current access level</span>
      </div>
      <div className="metric-grid">
        <MetricCard label="Environment" value={String(platform.environment ?? config.app_env ?? "development")} hint="Runtime" />
        <MetricCard label="API Key Present" value={String(config.openai_api_key_present ?? false)} hint="Boolean only" />
        <MetricCard label="Storage Root" value={String(config.storage_root ?? "data")} hint="Local persistence" />
        <MetricCard label="Config Health" value={String(health.status ?? "unknown")} hint={`${String(health.enabled_modules ?? 0)} enabled modules`} />
      </div>
      <ConfigurationCard title="Platform Configuration" description="Central platform settings and environment values.">
        <div className="metric-grid">
          <MetricCard label="Platform" value={String(platform.platform_name ?? "AI Marketing Content System")} hint={String(platform.version ?? "1.0.0")} />
          <MetricCard label="Maintenance" value={String(platform.maintenance_mode ?? false)} hint="Global mode" />
          <MetricCard label="Registration" value={String(platform.registration_enabled ?? true)} hint="User sign-up" />
          <MetricCard label="Workflow" value={String(platform.workflow_enabled ?? true)} hint="Module toggle" />
        </div>
        <JsonViewer data={platform} title="Platform JSON" />
      </ConfigurationCard>
      <ConfigurationCard title="Feature Flags" description="Centralized platform feature toggles.">
        {!canManageConfig ? (
          <div className="panel panel--muted">
            <p className="panel__title">Read-only mode</p>
            <p className="muted">Your current role can review configuration, but editing requires manager or admin access.</p>
          </div>
        ) : null}
        <div className="row wrap">
          {Object.entries((editableFlags && Object.keys(editableFlags).length ? editableFlags : (flags as Record<string, boolean>)) as Record<string, boolean>).map(([flag, enabled]) => (
            <div key={flag} className="row wrap">
              <FeatureFlagBadge label={flag} enabled={enabled} />
              {canManageConfig ? (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void handleToggleFlag(flag, !enabled)}
                >
                  {enabled ? "Disable" : "Enable"}
                </Button>
              ) : null}
            </div>
          ))}
        </div>
        {updateMessage ? <p className="muted">{updateMessage}</p> : null}
        <JsonViewer data={editableFlags && Object.keys(editableFlags).length ? editableFlags : flags} title="Feature Flags JSON" />
      </ConfigurationCard>
      <ConfigurationCard title="Modules" description="Enabled platform modules and descriptions.">
        <div className="stack">
          {modules.length ? modules.map((module: any) => (
            <div className="metric-card" key={String(module.module)}>
              <p className="metric-card__label">{String(module.module ?? "module")}</p>
              <p className="metric-card__value">{String(module.enabled ? "Enabled" : "Disabled")}</p>
              <p className="metric-card__hint">{String(module.description ?? "")}</p>
            </div>
          )) : <EmptyState title="No modules found" description="The module registry is empty." />}
        </div>
      </ConfigurationCard>
      <ConfigurationCard title="Limits" description="Informational platform limits and quotas.">
        <div className="metric-grid">
          <MetricCard label="Max Brands" value={String((limits as any).max_brands ?? "-")} hint="Informational" />
          <MetricCard label="Max Users" value={String((limits as any).max_users ?? "-")} hint="Informational" />
          <MetricCard label="Max Reports" value={String((limits as any).max_reports ?? "-")} hint="Informational" />
          <MetricCard label="Max Workflows" value={String((limits as any).max_workflows ?? "-")} hint="Informational" />
        </div>
      </ConfigurationCard>
      <ConfigurationCard title="Environment" description="Development, staging, or production settings.">
        <div className="metric-grid">
          <MetricCard label="Environment" value={String(environment.environment ?? platform.environment ?? "development")} hint="Mode" />
          <MetricCard label="Debug" value={String(environment.debug ?? false)} hint="Runtime" />
          <MetricCard label="Stack Traces" value={String(environment.show_stack_traces ?? false)} hint="Debugging" />
          <MetricCard label="Enabled Flags" value={String(health.enabled_flags ?? Object.values(flags).filter(Boolean).length)} hint="Count" />
        </div>
      </ConfigurationCard>
      <ConfigurationCard title="Configuration Health" description="Central health summary for the SaaS config layer.">
        <div className="metric-grid">
          <MetricCard label="Health Status" value={String(health.status ?? "unknown")} hint={String(health.environment ?? platform.environment ?? "development")} />
          <MetricCard label="Enabled Modules" value={String(health.enabled_modules ?? modules.filter((module: any) => module.enabled).length)} hint="Registry" />
          <MetricCard label="Enabled Flags" value={String(health.enabled_flags ?? Object.values(flags).filter(Boolean).length)} hint="Feature flags" />
          <MetricCard label="Valid" value={String(health.valid ?? false)} hint="Validation" />
        </div>
        {Array.isArray(health.warnings) && health.warnings.length ? (
          <div className="section">
            <h3>Health Warnings</h3>
            <ul className="simple-list">
              {health.warnings.slice(0, 3).map((warning: string, index: number) => (
                <li key={`${warning}-${index}`}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </ConfigurationCard>
      <SecurityStatusCard
        securityStatus={securityStatus ?? null}
        securityHealth={securityHealth ?? null}
        securityFindings={securityFindings ?? null}
        securityDependencies={securityDependencies ?? null}
        securityConfiguration={securityConfiguration ?? null}
      />
      <ConfigurationCard title="Observability" description="Safe runtime visibility and request-level diagnostics.">
        <div className="metric-grid">
          <MetricCard label="Health" value={observabilityHealthStatus} hint="Observability" />
          <MetricCard label="System Status" value={String((observabilityStatus as any)?.observability ?? observabilityHealthStatus)} hint="Unified status" />
          <MetricCard label="Requests" value={String(observabilityMetricsData.total_requests ?? 0)} hint={`${String(observabilityMetricsData.error_count ?? 0)} errors`} />
          <MetricCard label="Avg Latency" value={`${String(observabilityMetricsData.average_response_time_ms ?? 0)} ms`} hint="Requests" />
          <MetricCard label="Workflow Runs" value={String(workflowSummary.workflow_runs ?? 0)} hint={String(workflowSummary.workflow_failures ?? 0)} />
          <MetricCard label="Storage Writable" value={String(storageSummary.storage_root_writable ?? false)} hint={String(storageSummary.record_count ?? 0)} />
          <MetricCard label="Uptime" value={`${String(Math.round(Number(runtime.process_uptime_seconds ?? 0)))}s`} hint={String(runtime.app_env ?? "development")} />
        </div>
        <div className="metric-grid">
          <MetricCard label="Observability Enabled" value={String(observabilityConfigData.observability_enabled ?? true)} hint="Config" />
          <MetricCard label="Request Logging" value={String(observabilityConfigData.request_logging_enabled ?? true)} hint="Config" />
          <MetricCard label="Error Tracking" value={String(observabilityConfigData.error_tracking_enabled ?? true)} hint="Config" />
          <MetricCard label="Runtime Metrics" value={String(observabilityConfigData.runtime_metrics_enabled ?? true)} hint="Config" />
        </div>
        {observabilityDomainItems.length ? (
          <div className="section">
            <h3>Metric Domains</h3>
            <ul className="simple-list">
              {observabilityDomainItems.slice(0, 6).map((domain: any) => (
                <li key={String(domain.domain ?? "domain")}>{String(domain.domain ?? "domain")} | {Object.keys(domain.metrics ?? {}).length} metrics</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="grid-2">
          <div className="section">
            <h3>Token Observability</h3>
            <JsonViewer data={observabilityTokensData} title="Token Metrics JSON" />
          </div>
          <div className="section">
            <h3>Cost Observability</h3>
            <JsonViewer data={observabilityCostsData} title="Cost Metrics JSON" />
          </div>
        </div>
        {Array.isArray(observabilityHealth?.warnings) && observabilityHealth.warnings.length ? (
          <div className="section">
            <h3>Observability Warnings</h3>
            <ul className="simple-list">
              {observabilityHealth.warnings.slice(0, 3).map((warning: string, index: number) => (
                <li key={`${warning}-${index}`}>{warning}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {recentErrorItems.length ? (
          <div className="section">
            <h3>Recent Errors</h3>
            <ul className="simple-list">
              {recentErrorItems.slice(0, 3).map((error, index: number) => (
                <li key={String(error.error_id ?? index)}>
                  {String(error.error_type ?? "error")} | {String(error.module ?? "module")} | {String(error.message ?? "")}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </ConfigurationCard>
      <ConfigurationCard title="Brand Management" description="Available brands, active selection, and validation status.">
        <div className="metric-grid">
          <MetricCard label="Active Brand" value={String(activeBrand ?? config.default_brand ?? "-")} hint={String(brandProfile?.display_name ?? "Selected")} />
          <MetricCard label="Brand Status" value={String(brandProfile?.status ?? brandValidationData?.valid ?? "unknown")} hint={String(brandProfile?.knowledge_path ?? "brand")} />
          <MetricCard label="Health Score" value={String(brandProfile?.health_score ?? "-")} hint={String(brandProfile?.health_status ?? "health")} />
          <MetricCard label="Default Platform" value={String(brandDefaults?.default_platform ?? config.default_platform ?? "instagram")} hint="Brand defaults" />
          <MetricCard label="Default Content" value={String(brandDefaults?.default_content_type ?? config.default_content_type ?? "instagram_post")} hint="Brand defaults" />
        </div>
        {brands?.length ? (
          <JsonViewer data={{ activeBrand, brands }} title="Brands JSON" />
        ) : (
          <EmptyState title="No brands found" description="Create a brand folder under brands/ to start." />
        )}
      </ConfigurationCard>
      <ConfigurationCard title="Organization Access" description="Current organization context and membership summary.">
        {!canManageConfig ? (
          <div className="panel panel--muted">
            <p className="panel__title">Read-only mode</p>
            <p className="muted">Your current role can review organization settings, but editing requires manager or admin access.</p>
          </div>
        ) : null}
        <OrganizationCard organization={organizationProfile ?? null} />
        <div className="metric-grid">
          <MetricCard label="Active Organization" value={String(activeOrganizationId ?? "none")} hint="Selected in the top bar" />
          <MetricCard label="Active Team" value={String(activeTeamId ?? "none")} hint="Selected in the top bar" />
          <MetricCard label="Organizations" value={String(organizations?.length ?? 0)} hint="Accessible orgs" />
          <MetricCard label="Members" value={String(organizationMembers?.length ?? 0)} hint="Accessible members" />
        </div>
      </ConfigurationCard>
      <ConfigurationCard title="Configuration Snapshot" description="Full safe configuration snapshot.">
        <JsonViewer data={config} title="Config JSON" />
      </ConfigurationCard>
    </div>
  );
}
