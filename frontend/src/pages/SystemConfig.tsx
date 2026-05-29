import { Card } from "../components/Card";
import { EmptyState } from "../components/EmptyState";
import { JsonViewer } from "../components/JsonViewer";
import { MetricCard } from "../components/MetricCard";
import { SectionHeader } from "../components/SectionHeader";
import type { WorkspaceProps } from "./shared";

interface SystemConfigProps extends WorkspaceProps {}

export function SystemConfig({ config, activeBrand, brandProfile, brandValidation, brandDefaults, brands }: SystemConfigProps) {
  if (!config) {
    return (
      <Card>
        <SectionHeader title="System Config" description="Safe runtime configuration and feature flags." />
        <EmptyState title="Config unavailable" description="Refresh the configuration to inspect safe runtime settings." />
      </Card>
    );
  }

  const flags = config.feature_flags ?? {};
  const brandValidationData = brandValidation as any;

  return (
    <div className="stack">
      <SectionHeader title="System Config" description="Safe runtime configuration summary with secrets removed." />
      <div className="metric-grid">
        <MetricCard label="Environment" value={String(config.app_env ?? "development")} hint="Runtime" />
        <MetricCard label="API Key Present" value={String(config.openai_api_key_present ?? false)} hint="Boolean only" />
        <MetricCard label="Storage Root" value={String(config.storage_root ?? "data")} hint="Local persistence" />
        <MetricCard label="API Debug" value={String(config.api_debug ?? false)} hint="Debug mode" />
      </div>
      <Card>
        <SectionHeader title="Feature Flags" description="Enabled modules and safe defaults." />
        <JsonViewer data={flags} title="Feature Flags JSON" />
      </Card>
      <Card>
        <SectionHeader title="Brand Management" description="Available brands, active selection, and validation status." />
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
      </Card>
      <Card>
        <SectionHeader title="Configuration" description="Full safe configuration snapshot." />
        <JsonViewer data={config} title="Config JSON" />
      </Card>
    </div>
  );
}
