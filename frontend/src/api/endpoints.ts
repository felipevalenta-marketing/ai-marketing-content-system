export const API_ENDPOINTS = {
  health: "/health",
  config: "/config",
  generate: "/generate",
  workflow: "/workflow",
  campaign: "/campaign",
  assets: "/assets",
  markdownReport: "/reports/markdown",
  latestReports: "/reports/latest",
  storageRecords: "/storage/records",
} as const;

export const REPORT_TYPES = [
  "workflow_report",
  "campaign_report",
  "generation_report",
  "asset_report",
  "executive_summary",
  "tracking_report",
  "cost_report",
  "media_report",
] as const;

export const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", hint: "Overview" },
  { id: "content", label: "Content Studio", hint: "Generate" },
  { id: "workflow", label: "Workflow Center", hint: "Orchestrate" },
  { id: "campaign", label: "Campaign Studio", hint: "Compose" },
  { id: "assets", label: "Asset Studio", hint: "Coordinate" },
  { id: "reports", label: "Reports Center", hint: "Markdown" },
  { id: "storage", label: "Storage Explorer", hint: "Browse" },
  { id: "analytics", label: "Analytics Center", hint: "Metrics" },
  { id: "governance", label: "Governance Center", hint: "Review" },
  { id: "config", label: "System Config", hint: "Settings" },
] as const;
