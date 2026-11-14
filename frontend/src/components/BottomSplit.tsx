"use client";

import React from "react";
import { ReviewRun, Repository } from "@/lib/types";
import { Terminal, BarChart2 } from "lucide-react";

interface BottomSplitProps {
  failedReview?: ReviewRun | null;
  reviews?: ReviewRun[];
  repositories?: Repository[];
}

export function BottomSplit({
  failedReview,
  reviews = [],
  repositories = [],
}: BottomSplitProps) {
  // Resolve repository full name
  const getRepoName = (repoId: string) => {
    const r = repositories.find((x) => x.id === repoId);
    return r ? r.full_name : "pr-sentinel/monitored-repo";
  };

  const activeReview = failedReview || (reviews.length > 0 ? reviews[0] : null);

  const now = new Date();
  const dayBuckets = Array.from({ length: 14 }).map((_, i) => {
    const d = new Date(now);
    d.setDate(d.getDate() - (13 - i));
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const dateKey = `${year}-${month}-${day}`; // YYYY-MM-DD
    const dayLabel = d.toLocaleDateString("en-US", { weekday: "narrow" });
    const fullDateStr = d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    return { dateKey, dayLabel, fullDateStr };
  });

  const daysData = dayBuckets.map(({ dateKey, dayLabel, fullDateStr }) => {
    const dayReviews = reviews.filter((r) => {
      if (!r.created_at) return false;
      try {
        const reviewDate = new Date(r.created_at).toISOString().slice(0, 10);
        return reviewDate === dateKey;
      } catch {
        return false;
      }
    });

    const count = dayReviews.length;
    const reqChangesCount = dayReviews.filter(
      (r) => r.verdict === "REQUEST_CHANGES" || r.status === "FAILED",
    ).length;
    const approvedCount = dayReviews.filter(
      (r) => r.verdict === "APPROVE",
    ).length;

    return {
      dateKey,
      dayLabel,
      fullDateStr,
      count,
      reqChangesCount,
      approvedCount,
      hasFail: reqChangesCount > 0,
    };
  });

  const maxDailyCount = Math.max(...daysData.map((d) => d.count), 1);
  const totalScans = reviews.length;
  const totalApproved = reviews.filter((r) => r.verdict === "APPROVE").length;
  const totalChangesReq = reviews.filter(
    (r) => r.verdict === "REQUEST_CHANGES" || r.status === "FAILED",
  ).length;
  const dailyMean = (totalScans / 14).toFixed(1);

  // Status tag for Card 1 header
  let auditStatusTag = "STANDBY";
  let isFailureTag = false;
  if (activeReview) {
    if (
      activeReview.verdict === "REQUEST_CHANGES" ||
      activeReview.status === "FAILED"
    ) {
      auditStatusTag = "VERIFIER_REJECT";
      isFailureTag = true;
    } else if (activeReview.verdict === "APPROVE") {
      auditStatusTag = "POLICY_APPROVED";
    } else if (activeReview.status === "PROCESSING") {
      auditStatusTag = "IN_FLIGHT";
    } else {
      auditStatusTag = "QUEUED";
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm flex flex-col justify-between overflow-hidden">
        <div>
          {/* Header */}
          <div className="px-4 py-2.5 border-b border-[var(--hairline)] flex items-center justify-between bg-[var(--surface-subtle)]">
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[var(--ink-secondary)]" />
              <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-primary)] uppercase">
                Last Security Advisory &bull; Audit Trail
              </span>
            </div>
            <span
              className={`text-[10px] font-mono font-semibold ${
                isFailureTag
                  ? "text-[var(--signal-red)]"
                  : "text-[var(--ink-secondary)]"
              }`}
            >
              {auditStatusTag}
            </span>
          </div>

          {/* Dynamic Mono Log Excerpt */}
          <div className="p-3.5 font-mono text-[11px] leading-relaxed select-text space-y-1.5 bg-[var(--canvas)] text-[var(--ink-secondary)] border-b border-[var(--hairline)] max-h-56 overflow-y-auto">
            {activeReview ? (
              <>
                <div className="text-[var(--ink-muted)]">
                  [{new Date(activeReview.created_at).toISOString()}] [worker]
                  job_id: arq:review_pull_request:{activeReview.id.slice(0, 8)}
                </div>

                <div>
                  [{new Date(activeReview.created_at).toISOString()}] [target]{" "}
                  {getRepoName(activeReview.repository_id)} &bull; PR #
                  {activeReview.pull_number} (@{activeReview.pr_author})
                </div>

                <div>
                  [ast_engine] Tree-sitter AST &amp; Diff parser analyzed commit{" "}
                  {activeReview.commit_sha.slice(0, 7)}
                </div>

                {activeReview.findings && activeReview.findings.length > 0 ? (
                  activeReview.findings.map((f, idx) => (
                    <div key={f.id || idx} className="space-y-0.5">
                      <div className="text-[var(--signal-red)] font-medium bg-[var(--signal-red-bg)] px-1.5 py-0.5 rounded-xs border-l-2 border-[var(--signal-red)]">
                        [{f.severity}] {f.category}: {f.title} ({f.file_path}
                        {f.line_start ? `:L${f.line_start}` : ""})
                      </div>
                      {f.verification_reason && (
                        <div className="text-[var(--ink-muted)] pl-2 text-[10px]">
                          &rarr; [VERIFIER]{" "}
                          {f.is_verified
                            ? "Confirmed exploitability"
                            : "Candidate"}
                          : {f.verification_reason}
                        </div>
                      )}
                      {f.cve_id && (
                        <div className="text-[var(--signal-red)] pl-2 text-[10px]">
                          &rarr; [OSV] Advisory {f.cve_id} in{" "}
                          {f.package_name || "manifest"}
                        </div>
                      )}
                    </div>
                  ))
                ) : activeReview.error_message ? (
                  <div className="text-[var(--signal-red)] font-medium bg-[var(--signal-red-bg)] px-1.5 py-0.5 rounded-xs border-l-2 border-[var(--signal-red)]">
                    [ERROR] {activeReview.error_message}
                  </div>
                ) : (
                  <>
                    <div className="text-[var(--ink-primary)]">
                      [policy_gate] Repository policy evaluated. Zero violations
                      detected.
                    </div>
                    <div className="text-[var(--ink-muted)]">
                      [verifier] All diff hunks passed adversarial verification.
                    </div>
                  </>
                )}

                <div className="text-[var(--ink-primary)] pt-1">
                  [
                  {new Date(
                    activeReview.completed_at || activeReview.created_at,
                  ).toISOString()}
                  ] [publisher] GitHub verdict:{" "}
                  {activeReview.verdict || activeReview.status}
                  {activeReview.execution_time_ms
                    ? ` (${(activeReview.execution_time_ms / 1000).toFixed(2)}s)`
                    : ""}
                </div>
              </>
            ) : (
              <>
                <div className="text-[var(--ink-muted)]">
                  [{now.toISOString()}] [daemon] PR-Sentinel security daemon
                  initialized and active.
                </div>
                <div>
                  [{now.toISOString()}] [webhook] Listening on
                  /api/v1/webhooks/github for pull_request events.
                </div>
                <div>
                  [{now.toISOString()}] [repositories] {repositories.length}{" "}
                  repository registered for automated audit.
                </div>
                <div className="text-[var(--ink-primary)]">
                  [status] Standby: Open or synchronize a Pull Request on GitHub
                  to trigger audit.
                </div>
              </>
            )}
          </div>
        </div>

        <div className="px-4 py-2 text-[10px] font-mono text-[var(--ink-muted)] flex items-center justify-between bg-[var(--surface)]">
          <span className="truncate max-w-[65%]">
            {activeReview?.findings && activeReview.findings.length > 0
              ? `Target: ${activeReview.findings[0].file_path}${activeReview.findings[0].line_start ? `:L${activeReview.findings[0].line_start}` : ""}`
              : activeReview
                ? `Target: Commit ${activeReview.commit_sha.slice(0, 7)}`
                : "Target: Standby"}
          </span>
          <span>
            {activeReview
              ? `Verified Findings: ${activeReview.findings?.filter((f) => f.is_verified).length || 0} / ${activeReview.total_findings || 0}`
              : "Zero Violations"}
          </span>
        </div>
      </div>

      <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm flex flex-col justify-between overflow-hidden">
        <div>
          <div className="px-4 py-2.5 border-b border-[var(--hairline)] flex items-center justify-between bg-[var(--surface-subtle)]">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-3.5 h-3.5 text-[var(--ink-secondary)]" />
              <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-primary)] uppercase">
                Reviews Stream &bull; Last 14 Days
              </span>
            </div>
            <span className="text-[10px] font-mono text-[var(--ink-secondary)]">
              Total {totalScans} Scan{totalScans === 1 ? "" : "s"}
            </span>
          </div>

          <div className="p-4 bg-[var(--canvas)] border-b border-[var(--hairline)]">
            <div className="h-36 flex items-end justify-between gap-1.5 pt-6 pb-2">
              {daysData.map((day, idx) => {
                const heightPercent =
                  day.count === 0
                    ? 3
                    : Math.max(
                        16,
                        Math.round((day.count / maxDailyCount) * 100),
                      );

                return (
                  <div
                    key={idx}
                    className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
                  >
                    <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none text-[9px] font-mono px-1.5 py-0.5 bg-[var(--ink-primary)] text-[var(--canvas)] rounded-xs whitespace-nowrap z-20 shadow-sm">
                      {day.fullDateStr}: {day.count} review
                      {day.count === 1 ? "" : "s"}
                      {day.hasFail
                        ? ` (${day.reqChangesCount} req changes)`
                        : ""}
                    </div>

                    <div
                      className={`w-full rounded-xs transition-all ${
                        day.count === 0
                          ? "bg-[var(--hairline-strong)] h-[2px]"
                          : day.hasFail
                            ? "bg-[var(--signal-red)] hover:opacity-90"
                            : "bg-[var(--ink-primary)] hover:opacity-80"
                      }`}
                      style={{
                        height: day.count === 0 ? "2px" : `${heightPercent}%`,
                      }}
                    />

                    <span className="text-[9px] font-mono text-[var(--ink-muted)] group-hover:text-[var(--ink-primary)] transition-colors truncate">
                      {day.dayLabel}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="px-4 py-2 text-[10px] font-mono text-[var(--ink-muted)] flex items-center justify-between bg-[var(--surface)]">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-xs bg-[var(--ink-primary)]" />
              <span>Approved ({totalApproved})</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-xs bg-[var(--signal-red)]" />
              <span>Req Changes ({totalChangesReq})</span>
            </div>
          </div>
          <span>Mean: {dailyMean}/day</span>
        </div>
      </div>
    </div>
  );
}
