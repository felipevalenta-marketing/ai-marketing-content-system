export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T | null;
  warnings: string[];
  errors: string[];
  metadata: Record<string, unknown>;
}

export interface HealthResponseData {
  status?: string;
  service?: string;
  version?: string;
  modules?: Record<string, boolean>;
  [key: string]: unknown;
}

export interface ObservabilityHealthCheck {
  status?: string;
  detail?: string;
  warnings?: string[];
  errors?: string[];
  workflow_runs?: number;
  [key: string]: unknown;
}

export interface ObservabilityHealthData {
  status?: string;
  health_score?: number;
  health_status?: string;
  system_status?: Record<string, string>;
  configuration?: Record<string, boolean>;
  checks?: Record<string, ObservabilityHealthCheck>;
  warnings?: string[];
  errors?: string[];
  timestamp?: string;
  sections?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ObservabilityStatusData {
  api?: string;
  storage?: string;
  auth?: string;
  rbac?: string;
  brands?: string;
  organizations?: string;
  workflows?: string;
  analytics?: string;
  configuration?: string;
  observability?: string;
  [key: string]: unknown;
}

export interface ObservabilityDomainData {
  domain?: string;
  metrics?: Record<string, unknown>;
}

export interface ObservabilityDomainsData {
  domains?: ObservabilityDomainData[];
  count?: number;
  [key: string]: unknown;
}

export interface TokenObservabilityData {
  domain?: string;
  metrics?: {
    total?: number;
    total_tokens?: number;
    by_workflow?: Record<string, number>;
    by_organization?: Record<string, number>;
    by_brand?: Record<string, number>;
    by_scope?: Record<string, number>;
  };
  [key: string]: unknown;
}

export interface CostObservabilityData {
  domain?: string;
  metrics?: {
    total?: number;
    total_cost?: number;
    by_workflow?: Record<string, number>;
    by_organization?: Record<string, number>;
    by_brand?: Record<string, number>;
    by_scope?: Record<string, number>;
  };
  [key: string]: unknown;
}

export interface ObservabilityConfigurationData {
  observability_enabled?: boolean;
  request_logging_enabled?: boolean;
  error_tracking_enabled?: boolean;
  runtime_metrics_enabled?: boolean;
  workflow_monitoring_enabled?: boolean;
  [key: string]: unknown;
}

export interface ObservabilityMetricsData {
  total_requests?: number;
  requests_by_path?: Record<string, number>;
  requests_by_status?: Record<string, number>;
  error_count?: number;
  average_response_time_ms?: number;
  workflow_runs?: number;
  workflow_failures?: number;
  storage_errors?: number;
  token_usage_total?: number;
  cost_total?: number;
  auth_failures?: number;
  domains?: string[];
  durations?: Record<string, Record<string, unknown>>;
  counters?: Record<string, Record<string, number>>;
  [key: string]: unknown;
}

export interface RuntimeDiagnosticsData {
  python_version?: string;
  app_env?: string;
  platform?: string;
  process_uptime_seconds?: number;
  storage_root_exists?: boolean;
  storage_root_writable?: boolean;
  enabled_modules?: Record<string, boolean>;
  log_level?: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface RecentErrorEntry {
  error_id?: string;
  timestamp?: string;
  error_type?: string;
  module?: string;
  message?: string;
  request_id?: string;
  workflow_id?: string;
  severity?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ErrorSummaryData {
  total_errors?: number;
  by_type?: Record<string, number>;
  by_module?: Record<string, number>;
  by_severity?: Record<string, number>;
}

export interface ObservabilityErrorsData {
  recent_errors?: RecentErrorEntry[];
  summary?: ErrorSummaryData;
  [key: string]: unknown;
}

export interface WorkflowObservabilityData {
  workflow_runs?: number;
  workflow_failures?: number;
  recent_workflows?: Array<Record<string, unknown>>;
  status_breakdown?: Record<string, number>;
  workflow_metrics?: Record<string, unknown>;
  workflow_summary?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface StorageObservabilityData {
  storage_root_exists?: boolean;
  storage_root_writable?: boolean;
  record_count?: number;
  latest_record_timestamp?: string;
  recent_records?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export interface ConfigResponseData {
  app_env?: string;
  openai_api_key_present?: boolean;
  default_model?: string;
  default_temperature?: number;
  default_max_output_tokens?: number;
  feature_flags?: Record<string, unknown>;
  supported_platforms?: string[];
  supported_content_types?: string[];
  storage_root?: string;
  default_brand?: string;
  default_platform?: string;
  default_content_type?: string;
  default_campaign_type?: string;
  default_visual_style?: string;
  default_image_aspect_ratio?: string;
  default_video_duration?: string;
  default_video_type?: string;
  default_creative_direction_type?: string;
  default_visual_identity?: string;
  enable_api_layer?: boolean;
  enable_frontend_demo?: boolean;
  api_debug?: boolean;
  enable_authentication?: boolean;
  enable_rbac?: boolean;
  default_user_role?: string;
  first_user_admin?: boolean;
  jwt_expiration_hours?: number;
  user_storage_path?: string;
  cors_origins?: string[];
  enable_multi_brand_management?: boolean;
  brand_root?: string;
  require_valid_brand?: boolean;
  enable_analytics?: boolean;
  analytics_default_type?: string;
  analytics_include_storage?: boolean;
  analytics_include_tokens?: boolean;
  analytics_include_costs?: boolean;
  analytics_include_governance?: boolean;
  configuration?: ConfigurationSummaryData;
  configuration_health?: ConfigurationHealthData;
  platform_config?: PlatformConfigData;
  feature_flags?: Record<string, boolean>;
  modules?: ModuleRegistryEntry[];
  limits?: LimitsData;
  environment?: EnvironmentConfigData;
  [key: string]: unknown;
}

export interface PlatformConfigData {
  platform_name?: string;
  environment?: string;
  version?: string;
  maintenance_mode?: boolean;
  registration_enabled?: boolean;
  analytics_enabled?: boolean;
  storage_enabled?: boolean;
  workflow_enabled?: boolean;
  reporting_enabled?: boolean;
  metadata?: Record<string, unknown>;
}

export interface ModuleRegistryEntry {
  module?: string;
  enabled?: boolean;
  description?: string;
}

export interface LimitsData {
  max_brands?: number;
  max_users?: number;
  max_reports?: number;
  max_workflows?: number;
  max_storage_records?: number;
}

export interface EnvironmentConfigData {
  environment?: string;
  debug?: boolean;
  show_stack_traces?: boolean;
}

export interface ConfigurationHealthData {
  enabled_modules?: number;
  enabled_flags?: number;
  environment?: string;
  valid?: boolean;
  status?: string;
  warnings?: string[];
  errors?: string[];
}

export interface ConfigurationSummaryData {
  platform_config?: PlatformConfigData;
  feature_flags?: Record<string, boolean>;
  modules?: ModuleRegistryEntry[];
  limits?: LimitsData;
  environment?: EnvironmentConfigData;
  configuration_health?: ConfigurationHealthData;
  enabled_modules?: ModuleRegistryEntry[];
  enabled_flags?: string[];
  brand_overrides?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface DateRange {
  start?: string;
  end?: string;
}

export interface AnalyticsRequest {
  analytics_type: string;
  brand?: string;
  platform?: string;
  organization_id?: string;
  team_id?: string;
  date_range?: DateRange;
  filters?: Record<string, unknown>;
  include_storage?: boolean;
  include_tokens?: boolean;
  include_costs?: boolean;
  include_governance?: boolean;
  include_reports?: boolean;
  metadata?: Record<string, unknown>;
}

export interface AnalyticsKpi {
  label?: string;
  value?: string | number;
  unit?: string;
  status?: string;
  description?: string;
  metadata?: Record<string, unknown>;
}

export interface AnalyticsDashboardPayload {
  cards?: Array<Record<string, unknown>>;
  tables?: Record<string, Array<Record<string, unknown>>>;
  summaries?: Record<string, unknown>;
  recent_activity?: Array<Record<string, unknown>>;
  health?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
}

export interface AnalyticsResult {
  success?: boolean;
  analytics_type?: string;
  generated_at?: string;
  date_range?: DateRange;
  filters?: Record<string, unknown>;
  executive_summary?: Record<string, unknown>;
  kpis?: Record<string, Record<string, AnalyticsKpi>>;
  sections?: Record<string, unknown>;
  trends?: Record<string, unknown>;
  insights?: string[];
  recommendations?: string[];
  dashboard_payload?: AnalyticsDashboardPayload;
  warnings?: string[];
  errors?: string[];
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface AnalyticsSummaryData extends AnalyticsResult {}

export interface AnalyticsDashboardData extends AnalyticsDashboardPayload {
  summaries?: Record<string, unknown>;
}

export interface AnalyticsHealthData extends AnalyticsResult {
  status?: string;
  records_count?: number;
  workflow_count?: number;
}

export interface BrandDefaults {
  display_name?: string;
  default_platform?: string;
  default_content_type?: string;
  default_campaign_type?: string;
  default_objective?: string;
  default_audience?: string;
  default_visual_style?: string;
  default_language?: string;
  [key: string]: unknown;
}

export interface BrandProfile {
  success?: boolean;
  brand_id?: string;
  display_name?: string;
  status?: string;
  knowledge_path?: string;
  available_files?: string[];
  missing_recommended_files?: string[];
  recommended_files?: string[];
  optional_files?: string[];
  defaults?: BrandDefaults;
  configuration?: Record<string, unknown>;
  configuration_present?: boolean;
  health_score?: number;
  health_status?: string;
  health?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
  validation?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface BrandRegistryEntry extends BrandProfile {}

export interface BrandHealth {
  health_score?: number;
  health_status?: string;
  warnings?: string[];
  [key: string]: unknown;
}

export interface BrandRegistry {
  updated_at?: string;
  root_path?: string;
  count?: number;
  brands?: BrandRegistryEntry[];
  [key: string]: unknown;
}

export interface GenerateRequest {
  brand: string;
  platform: string;
  content_type: string;
  organization_id?: string;
  team_id?: string;
  objective: string;
  audience: string;
  location: string;
  property_type?: string;
  extra_notes?: string;
  report?: boolean;
  markdown?: boolean;
  persist?: boolean;
  dry_run?: boolean;
  [key: string]: unknown;
}

export interface WorkflowRequest {
  workflow_type: string;
  brand: string;
  platform: string;
  organization_id?: string;
  team_id?: string;
  platforms: string[];
  content_type: string;
  campaign_type: string;
  objective: string;
  audience: string;
  location: string;
  assets: string[];
  report?: boolean;
  persist?: boolean;
  dry_run?: boolean;
  [key: string]: unknown;
}

export interface CampaignRequest {
  brand: string;
  platform: string;
  organization_id?: string;
  team_id?: string;
  campaign_type: string;
  objective: string;
  audience: string;
  location: string;
  property_type?: string;
  platforms: string[];
  [key: string]: unknown;
}

export interface AssetRequest {
  brand: string;
  platform: string;
  organization_id?: string;
  team_id?: string;
  content_type: string;
  campaign_type: string;
  objective: string;
  assets: string[];
  visual_style?: string;
  creative_direction?: string;
  [key: string]: unknown;
}

export interface MarkdownReportRequest {
  report_type: string;
  title?: string;
  brand?: string;
  organization_id?: string;
  team_id?: string;
  platform?: string;
  campaign_type?: string;
  content_type?: string;
  workflow_result?: Record<string, unknown>;
  pipeline_result?: Record<string, unknown>;
  campaign_result?: Record<string, unknown>;
  asset_result?: Record<string, unknown>;
  governance_result?: Record<string, unknown>;
  token_summary?: Record<string, unknown>;
  cost_summary?: Record<string, unknown>;
  storage_summary?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
  [key: string]: unknown;
}

export interface StorageRecord {
  record_id?: string;
  record_type?: string;
  created_at?: string;
  updated_at?: string;
  brand?: string;
  brand_id?: string;
  organization_id?: string;
  team_id?: string;
  platform?: string;
  content_type?: string;
  campaign_type?: string;
  execution_id?: string;
  source_module?: string;
  payload?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
  [key: string]: unknown;
}

export interface WorkflowResult extends Record<string, unknown> {
  workflow_id?: string;
  workflow_type?: string;
  status?: string;
  steps?: Array<Record<string, unknown>>;
  workflow_snapshot?: Record<string, unknown>;
  workflow_state_history?: Array<Record<string, unknown>>;
  workflow_timeline?: Array<Record<string, unknown>>;
  workflow_status_transitions?: Array<Record<string, unknown>>;
  token_summary?: TokenSummary;
  cost_summary?: CostSummary;
  report_summary?: Record<string, unknown>;
  storage_summary?: Record<string, unknown>;
}

export interface TokenSummary {
  provider?: string;
  model?: string;
  input_tokens?: number;
  output_tokens?: number;
  cached_input_tokens?: number;
  total_tokens?: number;
  estimated?: boolean;
  source?: string;
  module_breakdown?: Record<string, unknown>;
  workflow_token_summary?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface CostSummary {
  provider?: string;
  model?: string;
  currency?: string;
  input_cost?: number;
  output_cost?: number;
  cached_input_cost?: number;
  total_cost?: number;
  estimated_cost?: boolean;
  pricing_found?: boolean;
  module_breakdown?: Record<string, unknown>;
  execution_cost_summary?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface GovernanceSummary {
  success?: boolean;
  approved?: boolean;
  status?: string;
  overall_score?: number;
  quality_score?: number;
  brand_score?: number;
  platform_score?: number;
  factual_safety_score?: number;
  warnings?: string[];
  errors?: string[];
  [key: string]: unknown;
}

export interface ApiErrorShape {
  detail?: string;
  message?: string;
  error?: string;
  [key: string]: unknown;
}

export interface UserProfile {
  user_id?: string;
  email?: string;
  display_name?: string;
  status?: "active" | "inactive" | "suspended" | string;
  role?: string;
  permissions?: string[];
  organizations?: string[];
  active_organization_id?: string;
  active_team_id?: string;
  created_at?: string;
  updated_at?: string;
  settings?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface AccessSummary {
  role?: string;
  role_label?: string;
  role_type?: string;
  role_level?: number;
  role_hierarchy?: Array<Record<string, unknown>>;
  permissions?: string[];
  access?: Record<string, boolean>;
  permission_domains?: Array<Record<string, unknown>>;
  summary?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
  metadata?: Record<string, unknown>;
}

export interface RoleInfo {
  role?: string;
  label?: string;
  description?: string;
  permissions?: string[];
  level?: number;
  type?: string;
  inherits_from?: string[];
}

export interface PermissionInfo {
  permission?: string;
  domain?: string;
  label?: string;
  description?: string;
}

export interface PermissionDomainInfo {
  domain?: string;
  label?: string;
  description?: string;
  permission_count?: number;
  permissions?: PermissionInfo[];
}

export interface AuthResult {
  success?: boolean;
  user?: UserProfile | Record<string, unknown> | null;
  access_token?: string;
  token_type?: string;
  warnings?: string[];
  errors?: string[];
  metadata?: Record<string, unknown>;
  access?: AccessSummary;
  [key: string]: unknown;
}

export interface OrganizationSettings {
  default_brand?: string;
  default_platform?: string;
  default_language?: string;
  timezone?: string;
  features?: Record<string, unknown>;
  limits?: Record<string, unknown>;
}

export interface OrganizationProfile {
  success?: boolean;
  organization_id?: string;
  name?: string;
  slug?: string;
  status?: "active" | "inactive" | "suspended" | string;
  owner_user_id?: string;
  settings?: OrganizationSettings;
  metadata?: Record<string, unknown>;
  team_count?: number;
  member_count?: number;
  brand_count?: number;
  active_brand_ids?: string[];
  health_score?: number;
  health_status?: string;
  teams?: TeamProfile[];
  members?: MembershipProfile[];
  brands?: BrandAccessProfile["brand_access"];
  health?: OrganizationHealth;
  tenant_ready?: boolean;
  tenant_configuration?: Record<string, unknown>;
  tenant_limits?: Record<string, unknown>;
  analytics?: Record<string, unknown>;
  role_bridge?: Record<string, string>;
  warnings?: string[];
  errors?: string[];
}

export interface OrganizationRegistryEntry extends OrganizationProfile {
  health_score?: number;
  health_status?: string;
}

export interface OrganizationHealth {
  health_score?: number;
  health_status?: string;
  warnings?: string[];
  metadata?: Record<string, unknown>;
}

export interface OrganizationContext {
  organization_id?: string;
  team_id?: string;
  brand_id?: string;
  tenant_ready?: boolean;
  organization?: OrganizationProfile;
  organization_profile?: OrganizationProfile;
  active_team?: TeamProfile;
  active_brand?: Record<string, unknown>;
  teams?: TeamProfile[];
  members?: MembershipProfile[];
  brands?: BrandAccessProfile["brand_access"];
  role_bridge?: Record<string, string>;
  metadata?: Record<string, unknown>;
  validation?: {
    valid?: boolean;
    warnings?: string[];
    errors?: string[];
  };
  health?: OrganizationHealth;
}

export interface OrganizationRegistry {
  success?: boolean;
  organizations?: OrganizationRegistryEntry[];
  count?: number;
  warnings?: string[];
  errors?: string[];
}

export interface TeamProfile {
  success?: boolean;
  team_id?: string;
  organization_id?: string;
  name?: string;
  slug?: string;
  status?: "active" | "inactive" | "archived" | string;
  metadata?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
}

export interface MembershipProfile {
  success?: boolean;
  membership_id?: string;
  organization_id?: string;
  team_id?: string;
  user_id?: string;
  role?: string;
  status?: string;
  metadata?: Record<string, unknown>;
  warnings?: string[];
  errors?: string[];
}

export interface BrandAccessProfile {
  success?: boolean;
  brand_access?: Array<Record<string, unknown>>;
  count?: number;
  warnings?: string[];
  errors?: string[];
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface UserProfileUpdateRequest {
  display_name?: string | null;
  settings?: Record<string, unknown>;
}

export interface UserRoleUpdateRequest {
  role: string;
}

export interface UserListResponse {
  users?: UserProfile[];
  count?: number;
}
