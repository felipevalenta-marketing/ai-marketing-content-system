export interface WorkflowStep {
  step_id?: string;
  step_type?: string;
  name?: string;
  status?: string;
  warnings?: string[];
  errors?: string[];
  [key: string]: unknown;
}

export interface WorkflowSummary {
  workflow_id?: string;
  workflow_type?: string;
  status?: string;
  duration_seconds?: number;
  completed_steps?: number;
  failed_steps?: number;
  skipped_steps?: number;
  step_count?: number;
  [key: string]: unknown;
}
