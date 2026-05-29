export const DEFAULT_API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const PAGE_DESCRIPTIONS: Record<string, string> = {
  dashboard: "System overview and quick actions.",
  content: "Generate structured content through the backend pipeline.",
  workflow: "Run orchestration flows with governance and persistence.",
  campaign: "Compose campaign structures and deliverables.",
  assets: "Coordinate prompts, scripts, and asset readiness.",
  reports: "Render and preview professional markdown reports.",
  storage: "Inspect safe local persistence records.",
  analytics: "Review token, cost, and reporting summaries.",
  governance: "Inspect approval status and safety signals.",
  config: "Review safe runtime configuration.",
};

export const CONTENT_DEFAULTS = {
  brand: "wenzel_partner",
  platform: "instagram",
  content_type: "instagram_post",
  objective: "generate_leads",
  audience: "relocation_clients",
  location: "sant_llorenc_des_cardassar",
  property_type: "rustic_home",
};

export const WORKFLOW_DEFAULTS = {
  workflow_type: "full_campaign_package",
  brand: "wenzel_partner",
  platform: "instagram",
  platforms: ["instagram", "facebook", "linkedin"],
  content_type: "instagram_post",
  campaign_type: "property_launch",
  objective: "generate_leads",
  audience: "relocation_clients",
  location: "sant_llorenc_des_cardassar",
  assets: ["image_prompt", "video_prompt", "social_post"],
};

export const CAMPAIGN_DEFAULTS = {
  brand: "wenzel_partner",
  platform: "instagram",
  campaign_type: "property_launch",
  objective: "generate_leads",
  audience: "relocation_clients",
  location: "sant_llorenc_des_cardassar",
  property_type: "rustic_home",
  platforms: ["instagram", "facebook", "linkedin"],
};

export const ASSET_DEFAULTS = {
  brand: "wenzel_partner",
  platform: "instagram",
  content_type: "image_prompt",
  campaign_type: "property_launch",
  objective: "generate_leads",
  assets: ["image_prompt", "video_prompt", "social_post"],
  visual_style: "mediterranean_lifestyle",
  creative_direction: "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
};

export const ANALYTICS_DEFAULTS = {
  brand: "wenzel_partner",
  platform: "instagram",
  analytics_type: "executive_dashboard",
};
