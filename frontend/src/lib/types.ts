export type SeverityLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
export type FindingCategory = "CODE_SECURITY" | "DEPENDENCY_CVE" | "LICENSE";
export type ReviewStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
export type ReviewVerdict = "APPROVE" | "COMMENT" | "REQUEST_CHANGES";

export interface Policy {
  id: string;
  repository_id: string;
  fail_on_severity: SeverityLevel;
  block_prohibited_licenses: boolean;
  prohibited_licenses: string[];
  auto_request_changes: boolean;
  updated_at: string;
}

export interface Repository {
  id: string;
  github_repo_id: number;
  full_name: string;
  installation_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  policy?: Policy;
}

export interface Finding {
  id: string;
  review_run_id: string;
  category: FindingCategory;
  severity: SeverityLevel;
  title: string;
  description: string;
  file_path: string;
  line_start?: number;
  line_end?: number;
  code_snippet?: string;
  suggestion_markdown?: string;
  cve_id?: string;
  package_name?: string;
  current_version?: string;
  fixed_version?: string;
  is_verified: boolean;
  verification_reason?: string;
  published_inline: boolean;
  created_at: string;
}

export interface ReviewRun {
  id: string;
  repository_id: string;
  pull_number: number;
  commit_sha: string;
  title: string;
  pr_author: string;
  status: ReviewStatus;
  verdict?: ReviewVerdict;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_markdown?: string;
  error_message?: string;
  execution_time_ms?: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  findings?: Finding[];
}
