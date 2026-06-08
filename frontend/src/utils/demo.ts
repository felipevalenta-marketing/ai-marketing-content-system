import type {
  AccessSummary,
  AnalyticsDashboardData,
  AnalyticsHealthData,
  AnalyticsSummaryData,
  BrandDefaults,
  BrandProfile,
  BrandRegistryEntry,
  ConfigResponseData,
  HealthResponseData,
  OrganizationContext,
  OrganizationProfile,
  OrganizationRegistryEntry,
  ReleaseCertificationData,
  ReleaseChecklistData,
  ReleaseGovernanceData,
  ReleaseHealthData,
  ReleaseMaturityData,
  ReleaseReadinessData,
  ReleaseReportData,
  ReleaseScoreData,
  ReleaseStatusData,
  TeamProfile,
  UserProfile,
} from "../types/api";

export const IS_DEMO_MODE = String(import.meta.env?.VITE_DEMO_MODE ?? "").toLowerCase() === "true";

export const DEMO_BRAND_ID = "wenzel_partner";
export const DEMO_ORGANIZATION_ID = "demo_ironhack";
export const DEMO_TEAM_ID = "demo_team";

export const DEMO_USER: UserProfile = {
  user_id: "demo-admin",
  email: "demo@ironhack.local",
  display_name: "Demo Admin",
  status: "active",
  role: "admin",
  permissions: ["admin:all"],
  organizations: [DEMO_ORGANIZATION_ID],
  active_organization_id: DEMO_ORGANIZATION_ID,
  active_team_id: DEMO_TEAM_ID,
  settings: {
    demo_mode: true,
  },
};

export const DEMO_ACCESS: AccessSummary = {
  role: "admin",
  role_label: "Admin",
  permissions: ["admin:all"],
  access: {
    "admin:all": true,
  },
  summary: {
    mode: "demo",
  },
};

export const DEMO_CONFIG: ConfigResponseData = {
  app_env: "development",
  default_model: "gpt-4.1-mini",
  default_temperature: 0.7,
  default_max_output_tokens: 2048,
  storage_root: "data",
  default_brand: DEMO_BRAND_ID,
  default_platform: "instagram",
  default_content_type: "instagram_post",
  default_campaign_type: "property_launch",
  default_visual_style: "mediterranean_lifestyle",
  default_video_duration: "30s",
  feature_flags: {
    dashboard: true,
    content: true,
    campaign: true,
    analytics: true,
    governance: true,
    config: true,
  },
  supported_platforms: ["instagram", "facebook", "linkedin"],
  supported_content_types: ["instagram_post", "carousel", "reel"],
  enable_api_layer: true,
};

export const DEMO_HEALTH: HealthResponseData = {
  status: "healthy",
  service: "demo-api",
  version: "demo",
  modules: {
    dashboard: true,
    content: true,
    campaign: true,
    analytics: true,
    governance: true,
    config: true,
  },
};

export const DEMO_BRAND_PROFILE: BrandProfile = {
  brand_id: DEMO_BRAND_ID,
  display_name: "Wenzel Partner",
  status: "active",
  knowledge_path: "brands/wenzel_partner",
  health_score: 100,
  health_status: "healthy",
  markdown_count: 12,
  metadata: {
    demo_mode: true,
  },
};

export const DEMO_BRANDS: BrandRegistryEntry[] = [
  {
    ...DEMO_BRAND_PROFILE,
    available_files: ["brand.md", "voice.md", "visuals.md"],
  },
];

export const DEMO_BRAND_DEFAULTS: BrandDefaults = {
  default_platform: "instagram",
  default_content_type: "instagram_post",
  default_campaign_type: "property_launch",
  default_visual_style: "mediterranean_lifestyle",
  default_image_aspect_ratio: "4:5",
  default_video_duration: "30s",
  default_creative_direction_type: "luxury_lifestyle",
  default_visual_identity: "warm_sunlit_homes",
};

export const DEMO_ORGANIZATION_PROFILE: OrganizationRegistryEntry = {
  organization_id: DEMO_ORGANIZATION_ID,
  name: "Ironhack Demo Organization",
  slug: "ironhack-demo-organization",
  status: "active",
  owner_user_id: "demo-admin",
  team_count: 1,
  member_count: 1,
  brand_count: 1,
  active_brand_ids: [DEMO_BRAND_ID],
  health_score: 100,
  health_status: "healthy",
  settings: {
    default_brand: DEMO_BRAND_ID,
    default_platform: "instagram",
    default_language: "en",
    timezone: "Europe/Madrid",
    features: {
      demo_mode: true,
    },
  },
  metadata: {
    demo_mode: true,
  },
  warnings: [],
  errors: [],
};

export const DEMO_ORGANIZATION_CONTEXT: OrganizationContext = {
  organization_id: DEMO_ORGANIZATION_ID,
  team_id: DEMO_TEAM_ID,
  brand_id: DEMO_BRAND_ID,
  tenant_ready: true,
  organization: DEMO_ORGANIZATION_PROFILE,
  organization_profile: DEMO_ORGANIZATION_PROFILE,
  teams: [
    {
      team_id: DEMO_TEAM_ID,
      organization_id: DEMO_ORGANIZATION_ID,
      name: "Demo Growth Team",
      slug: "demo-growth-team",
      status: "active",
    },
  ],
  metadata: {
    demo_mode: true,
  },
};

export const DEMO_TEAMS: TeamProfile[] = [
  {
    team_id: DEMO_TEAM_ID,
    organization_id: DEMO_ORGANIZATION_ID,
    name: "Demo Growth Team",
    slug: "demo-growth-team",
    status: "active",
    metadata: {
      demo_mode: true,
    },
  },
];

export const DEMO_SNAPSHOTS = {
  generate: {
    status: "success",
    content_preview: "Demo content preview",
    token_summary: {
      input_tokens: 1240,
      output_tokens: 860,
      total_tokens: 2100,
      provider: "openai",
      model: "gpt-4o-mini",
    },
    cost_summary: {
      total_cost: 12.4,
      currency: "USD",
      estimated_cost: true,
    },
  },
  workflow: {
    status: "success",
    title: "Demo workflow",
    token_summary: {
      input_tokens: 1800,
      output_tokens: 1220,
      total_tokens: 3020,
      provider: "openai",
      model: "gpt-4o-mini",
    },
    cost_summary: {
      total_cost: 18.75,
      currency: "USD",
      estimated_cost: true,
    },
    markdown: "# Demo Workflow\nGenerated in demo mode.",
  },
  reports: {
    status: "available",
    markdown: "# Demo Report\nExecutive summary for presentation.",
  },
  storage: {
    count: 18,
    records: [
      { record_type: "generation", record_id: "demo-gen-1", created_at: "2026-05-30T08:30:00Z" },
      { record_type: "workflow", record_id: "demo-workflow-1", created_at: "2026-05-30T08:45:00Z" },
    ],
  },
} as const;

export const DEMO_ANALYTICS_SUMMARY: AnalyticsSummaryData = {
  success: true,
  executive_summary: {
    approval_status: "approved",
    headline: "Demo workspace is ready",
    outcome: "Presentation data is loaded without waiting for backend runtime data.",
  },
  kpis: {
    executive: {
      total_tokens: { value: 3020 },
      total_cost: { value: 18.75 },
      workflow_success_rate: { value: 0.98 },
      governance_approval_rate: { value: 0.97 },
    },
  },
  insights: [
    "Brand context is available for Wenzel Partner.",
    "Demo content pipeline is ready for presentations.",
    "Analytics cards are populated from local demo data.",
  ],
  recommendations: [
    "Run a workflow to refresh live analytics.",
    "Open reports to review the latest demo summary.",
  ],
  metadata: {
    records_collected: 24,
  },
};

export const DEMO_ANALYTICS_DASHBOARD: AnalyticsDashboardData = {
  cards: [
    { label: "Published Posts", value: "12", description: "Demo cadence", unit: "items" },
    { label: "Campaigns", value: "4", description: "Active demo campaigns", unit: "items" },
    { label: "Approval Rate", value: "97%", description: "Governance", unit: "%" },
    { label: "Estimated Cost", value: "$18.75", description: "Demo spend", unit: "USD" },
  ],
  recent_activity: [
    { record_id: "demo-activity-1", record_type: "generation", brand: DEMO_BRAND_ID, platform: "instagram", created_at: "2026-05-30T08:30:00Z" },
    { record_id: "demo-activity-2", record_type: "workflow", brand: DEMO_BRAND_ID, platform: "instagram", created_at: "2026-05-30T08:45:00Z" },
  ],
  summaries: {
    executive: {
      approval_status: "approved",
      headline: "Demo dashboard active",
      outcome: "Workspace, brand, and analytics cards are populated from local fallback data.",
    },
    insights: ["Demo mode bypasses protected endpoints.", "Brand and organization context are preloaded."],
    recommendations: ["Switch to live mode to connect the backend.", "Keep demo data for stakeholder walkthroughs."],
  },
  health: {
    status: "healthy",
    records_count: 24,
  },
};

export const DEMO_ANALYTICS_HEALTH: AnalyticsHealthData = {
  success: true,
  status: "healthy",
  records_count: 24,
  workflow_count: 2,
  executive_summary: {
    headline: "Demo analytics healthy",
  },
};

export const DEMO_RELEASE_STATUS: ReleaseStatusData = {
  success: true,
  release_status: "approved",
  release_score: 100,
  production_ready: true,
  certification_status: "approved",
  maturity_level: "production_ready",
};

export const DEMO_RELEASE_CERTIFICATION: ReleaseCertificationData = {
  success: true,
  mvp_certified: true,
  production_ready: true,
  certification_status: "approved",
  version: "1.0.0",
};

export const DEMO_RELEASE_MATURITY: ReleaseMaturityData = {
  success: true,
  maturity_score: 100,
  maturity_level: "production_ready",
};

export const DEMO_RELEASE_GOVERNANCE: ReleaseGovernanceData = {
  success: true,
  release_status: "approved",
  warnings: [],
  blocked_reasons: [],
};

export const DEMO_RELEASE_HEALTH: ReleaseHealthData = {
  success: true,
  overall_health: "healthy",
  health_score: 100,
};

export const DEMO_RELEASE_READINESS: ReleaseReadinessData = {
  success: true,
  mvp_ready: true,
  release_ready: true,
  production_ready: true,
};

export const DEMO_RELEASE_REPORT: ReleaseReportData = {
  success: true,
  report_path: "docs/MVP_READINESS_REPORT.md",
  report_title: "MVP Readiness Report",
};

export const DEMO_RELEASE_SCORE: ReleaseScoreData = {
  success: true,
  overall_score: 100,
  release_score: 100,
  release_status: "ready",
  domain_scores: {
    functionality: 100,
    frontend: 100,
    api: 100,
    storage: 100,
    reporting: 100,
    analytics: 100,
    authentication: 100,
    rbac: 100,
    organizations: 100,
    deployment: 100,
    observability: 100,
    security: 100,
    ci_cd: 100,
    documentation: 100,
  },
};

export const DEMO_RELEASE_CHECKLIST: ReleaseChecklistData = {
  success: true,
  total_checks: 150,
  passed: 150,
  failed: 0,
  warnings: 0,
};
