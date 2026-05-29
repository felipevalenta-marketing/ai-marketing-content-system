export type ReportType =
  | "workflow_report"
  | "campaign_report"
  | "generation_report"
  | "asset_report"
  | "executive_summary"
  | "tracking_report"
  | "cost_report"
  | "media_report";

export interface MarkdownReportData extends Record<string, unknown> {
  report_type?: ReportType | string;
  title?: string;
  markdown?: string;
  sections?: Array<Record<string, unknown> | string>;
  word_count?: number;
  export_path?: string;
  metadata?: Record<string, unknown>;
}
