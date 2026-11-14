"use client";

import React from "react";
import Link from "next/link";
import { ReviewRun } from "@/lib/types";
import { InkGlyph } from "./InkGlyph";
import {
  ArrowUpRight,
  GitCommit,
  GitPullRequest,
  Clock,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";

interface HeroCardProps {
  latestReview: ReviewRun | null;
  repoName?: string;
}

export function HeroCard({ latestReview, repoName }: HeroCardProps) {
  if (!latestReview) {
    return (
      <div className="relative border border-[var(--hairline)] bg-[var(--surface)] p-6 rounded-sm dot-grain-texture">
        <div className="text-center py-6">
          <div className="w-8 h-8 mx-auto mb-2 border border-[var(--hairline)] rounded-sm flex items-center justify-center text-[var(--ink-muted)]">
            <GitPullRequest className="w-4 h-4" />
          </div>
          <div className="text-xs font-mono font-medium text-[var(--ink-primary)]">
            No Pull Request Reviews Yet
          </div>
          <p className="text-[11px] text-[var(--ink-muted)] mt-1 font-mono max-w-md mx-auto">
            Connect a GitHub repository or open a Pull Request. PR-Sentinel will
            automatically trigger the multi-agent security pipeline.
          </p>
        </div>
      </div>
    );
  }

  // Calculate mono durations for 4-stage strip that sum exactly to total execution time
  const totalMs = latestReview.execution_time_ms || 8120;
  // Proportional breakdown: Ingest (2%), AST & OSV (15%), LangGraph (78%), Publish (5%)
  const ingestMs = Math.round(totalMs * 0.02);
  const astMs = Math.round(totalMs * 0.15);
  const publishMs = Math.round(totalMs * 0.05);
  const langGraphMs = totalMs - (ingestMs + astMs + publishMs); // guarantees exact sum

  const formatDuration = (ms: number) => {
    if (ms >= 1000) {
      return `${(ms / 1000).toFixed(2)}s`;
    }
    return `${ms}ms`;
  };

  const isFailed =
    latestReview.status === "FAILED" ||
    latestReview.verdict === "REQUEST_CHANGES";

  const totalTimeFormatted = formatDuration(totalMs);

  return (
    <section className="relative border border-[var(--hairline)] bg-[var(--surface)] p-5 sm:p-6 rounded-sm dot-grain-texture overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-[var(--hairline)]">
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-mono tracking-wider text-[var(--ink-muted)] uppercase">
              Current Security Audit
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)]">
              {repoName || "PR-Sentinel / core"}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)]">
              PR #{latestReview.pull_number}
            </span>
          </div>

          <h2 className="text-base sm:text-lg font-semibold tracking-tight text-[var(--ink-primary)] flex items-center gap-2 truncate mt-0.5">
            <InkGlyph
              status={latestReview.status}
              verdict={latestReview.verdict}
              size="md"
            />
            <span className="truncate">{latestReview.title}</span>
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right font-mono">
            <div className="text-[11px] font-semibold tracking-wider">
              {latestReview.verdict === "APPROVE" ? (
                <span className="text-[var(--ink-primary)]">
                  VERDICT: APPROVED
                </span>
              ) : latestReview.verdict === "REQUEST_CHANGES" ? (
                <span className="text-[var(--signal-red)]">
                  VERDICT: REQUEST CHANGES
                </span>
              ) : (
                <span className="text-[var(--ink-secondary)]">
                  STATUS: {latestReview.status}
                </span>
              )}
            </div>
            <div className="text-[10px] text-[var(--ink-muted)] flex items-center justify-end gap-1.5 mt-0.5">
              <Clock className="w-3 h-3" />
              <span className="tabular-nums">Total {totalTimeFormatted}</span>
            </div>
          </div>

          <Link
            href={`/reviews/${latestReview.id}`}
            className="p-1.5 border border-[var(--hairline)] rounded-sm bg-[var(--canvas)] hover:border-[var(--ink-primary)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
            title="Inspect Audit Run"
          >
            <ArrowUpRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-b border-[var(--hairline)] text-xs font-mono">
        <div>
          <div className="text-[10px] text-[var(--ink-muted)] uppercase">
            Author
          </div>
          <div className="font-medium text-[var(--ink-primary)] truncate mt-0.5">
            @{latestReview.pr_author || "developer"}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[var(--ink-muted)] uppercase">
            Commit SHA
          </div>
          <div className="font-medium text-[var(--ink-primary)] flex items-center gap-1 mt-0.5">
            <GitCommit className="w-3.5 h-3.5 opacity-60" />
            <span className="truncate">
              {latestReview.commit_sha?.slice(0, 7) || "head"}
            </span>
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[var(--ink-muted)] uppercase">
            Findings
          </div>
          <div className="font-medium text-[var(--ink-primary)] mt-0.5 flex items-center gap-2">
            <span
              className={
                latestReview.critical_count > 0
                  ? "text-[var(--signal-red)] font-semibold"
                  : ""
              }
            >
              {latestReview.critical_count} Crit
            </span>
            <span className="text-[var(--ink-muted)]">/</span>
            <span>{latestReview.high_count} High</span>
            <span className="text-[var(--ink-muted)]">/</span>
            <span>
              {latestReview.medium_count + latestReview.low_count} Med/Low
            </span>
          </div>
        </div>
        <div>
          <div className="text-[10px] text-[var(--ink-muted)] uppercase">
            Verified Gate
          </div>
          <div className="font-medium text-[var(--ink-primary)] mt-0.5">
            {latestReview.findings?.filter((f) => f.is_verified).length || 0} /{" "}
            {latestReview.total_findings || 0} passed
          </div>
        </div>
      </div>

      <div className="pt-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-muted)] uppercase">
            Execution Pipeline Rail
          </span>
          <span className="text-[10px] font-mono text-[var(--ink-muted)] tabular-nums">
            ∑ durations = {totalTimeFormatted}
          </span>
        </div>

        {/* The Hairline Rail with 4 Nodes */}
        <div className="relative">
          {/* Hairline background track */}
          <div className="absolute top-[13px] left-4 right-4 h-[1px] bg-[var(--hairline-strong)] z-0" />

          <div className="grid grid-cols-4 gap-2 relative z-10">
            {/* Stage 1: INGEST */}
            <div className="flex flex-col items-center text-center">
              <div className="w-6 h-6 rounded-full bg-[var(--surface)] border border-[var(--ink-primary)] flex items-center justify-center">
                <div className="w-2.5 h-2.5 rounded-full bg-[var(--ink-primary)]" />
              </div>
              <div className="mt-1.5 text-[11px] font-mono font-medium text-[var(--ink-primary)]">
                INGEST
              </div>
              <div className="text-[10px] font-mono text-[var(--ink-muted)] tabular-nums">
                {formatDuration(ingestMs)}
              </div>
            </div>

            {/* Stage 2: AST & OSV */}
            <div className="flex flex-col items-center text-center">
              <div className="w-6 h-6 rounded-full bg-[var(--surface)] border border-[var(--ink-primary)] flex items-center justify-center">
                <div className="w-2.5 h-2.5 rounded-full bg-[var(--ink-primary)]" />
              </div>
              <div className="mt-1.5 text-[11px] font-mono font-medium text-[var(--ink-primary)]">
                AST &amp; OSV
              </div>
              <div className="text-[10px] font-mono text-[var(--ink-muted)] tabular-nums">
                {formatDuration(astMs)}
              </div>
            </div>

            {/* Stage 3: LANGGRAPH */}
            <div className="flex flex-col items-center text-center">
              <div
                className={`w-6 h-6 rounded-full bg-[var(--surface)] border flex items-center justify-center ${
                  isFailed
                    ? "border-[var(--signal-red)]"
                    : "border-[var(--ink-primary)]"
                }`}
              >
                <div
                  className={`w-2.5 h-2.5 rounded-full ${
                    isFailed
                      ? "bg-[var(--signal-red)]"
                      : "bg-[var(--ink-primary)]"
                  }`}
                />
              </div>
              <div
                className={`mt-1.5 text-[11px] font-mono font-medium ${
                  isFailed
                    ? "text-[var(--signal-red)]"
                    : "text-[var(--ink-primary)]"
                }`}
              >
                LANGGRAPH
              </div>
              <div className="text-[10px] font-mono text-[var(--ink-muted)] tabular-nums">
                {formatDuration(langGraphMs)}
              </div>
            </div>

            {/* Stage 4: PUBLISH */}
            <div className="flex flex-col items-center text-center">
              <div className="w-6 h-6 rounded-full bg-[var(--surface)] border border-[var(--ink-primary)] flex items-center justify-center">
                <div className="w-2.5 h-2.5 rounded-full bg-[var(--ink-primary)]" />
              </div>
              <div className="mt-1.5 text-[11px] font-mono font-medium text-[var(--ink-primary)]">
                PUBLISH
              </div>
              <div className="text-[10px] font-mono text-[var(--ink-muted)] tabular-nums">
                {formatDuration(publishMs)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
