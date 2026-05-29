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
  enable_api_layer?: boolean;
  enable_frontend_demo?: boolean;
  api_debug?: boolean;
  cors_origins?: string[];
  enable_analytics?: boolean;
  analytics_default_type?: string;
  analytics_include_storage?: boolean;
  analytics_include_tokens?: boolean;
  analytics_include_costs?: boolean;
  analytics_include_governance?: boolean;
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

export interface GenerateRequest {
  brand: string;
  platform: string;
  content_type: string;
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
