"use client";

import React from "react";
import Link from "next/link";
import { ReviewRun, Repository } from "@/lib/types";
import { InkGlyph } from "./InkGlyph";
import { ArrowUpRight, GitPullRequest } from "lucide-react";

interface ReviewsTableProps {
  reviews: ReviewRun[];
  repositories: Repository[];
  isLoading?: boolean;
}

export function ReviewsTable({
  reviews,
  repositories,
  isLoading = false,
}: ReviewsTableProps) {
  const getRepoName = (repoId: string) => {
    const r = repositories.find((x) => x.id === repoId);
    return r ? r.full_name : "unknown/repo";
  };

  const formatRelativeTime = (dateStr: string) => {
    if (!dateStr) return "recently";
    try {
      const diffMs = Date.now() - new Date(dateStr).getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 1) return "just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      const diffDays = Math.floor(diffHours / 24);
      return `${diffDays}d ago`;
    } catch {
      return "recently";
    }
  };

  return (
    <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm overflow-hidden">
      {/* Table Title Bar */}
      <div className="px-4 py-3 border-b border-[var(--hairline)] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <GitPullRequest className="w-4 h-4 text-[var(--ink-secondary)]" />
          <h3 className="text-xs font-mono font-semibold tracking-wider text-[var(--ink-primary)] uppercase">
            Audit Stream &bull; Pull Request Reviews
          </h3>
        </div>
        <div className="text-[10px] font-mono text-[var(--ink-muted)]">
          {reviews.length} {reviews.length === 1 ? "entry" : "entries"} recorded
        </div>
      </div>

      {/* Responsive Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[var(--hairline)] bg-[var(--surface-subtle)] text-[10px] font-mono font-medium text-[var(--ink-muted)] uppercase tracking-wider">
              <th className="py-2.5 px-3 w-8 text-center">St</th>
              <th className="py-2.5 px-3">Pull Request</th>
              <th className="py-2.5 px-3">Repository</th>
              <th className="py-2.5 px-3">Author</th>
              <th className="py-2.5 px-3">Vulnerabilities</th>
              <th className="py-2.5 px-3 text-right">Duration</th>
              <th className="py-2.5 px-3 text-right">Executed</th>
              <th className="py-2.5 px-3 w-10 text-center"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--hairline)]">
            {isLoading && reviews.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="py-8 text-center text-xs font-mono text-[var(--ink-muted)]"
                >
                  <div className="flex items-center justify-center gap-2">
                    <InkGlyph type="processing" size="sm" />
                    <span>Querying review records...</span>
                  </div>
                </td>
              </tr>
            ) : reviews.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="py-8 text-center text-xs font-mono text-[var(--ink-muted)] italic"
                >
                  No security reviews found matching the current criteria.
                </td>
              </tr>
            ) : (
              reviews.map((rev) => {
                const isFailed =
                  rev.status === "FAILED" ||
                  rev.verdict === "REQUEST_CHANGES";

                return (
                  <tr
                    key={rev.id}
                    className={`group transition-colors hover:bg-[var(--surface-subtle)] ${
                      isFailed ? "bg-[var(--signal-red-bg)]" : ""
                    }`}
                  >
                    {/* Status Glyph */}
                    <td className="py-2.5 px-3 text-center align-middle">
                      <InkGlyph
                        status={rev.status}
                        verdict={rev.verdict}
                        size="sm"
                      />
                    </td>

                    {/* PR Title & Number */}
                    <td className="py-2.5 px-3 align-middle max-w-xs sm:max-w-md">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-medium text-[var(--ink-secondary)]">
                          #{rev.pull_number}
                        </span>
                        <Link
                          href={`/reviews/${rev.id}`}
                          className="font-medium text-[var(--ink-primary)] hover:underline truncate"
                          title={rev.title}
                        >
                          {rev.title}
                        </Link>
                      </div>
                    </td>

                    {/* Repository */}
                    <td className="py-2.5 px-3 align-middle">
                      <span className="font-mono text-[11px] px-1.5 py-0.5 rounded-xs border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)] truncate max-w-[140px] inline-block">
                        {getRepoName(rev.repository_id)}
                      </span>
                    </td>

                    {/* Author */}
                    <td className="py-2.5 px-3 align-middle font-mono text-[11px] text-[var(--ink-secondary)]">
                      @{rev.pr_author || "author"}
                    </td>

                    {/* Findings / Vulnerabilities */}
                    <td className="py-2.5 px-3 align-middle font-mono text-[11px]">
                      {rev.critical_count > 0 || rev.high_count > 0 ? (
                        <div className="flex items-center gap-1.5">
                          {rev.critical_count > 0 && (
                            <span className="text-[var(--signal-red)] font-semibold">
                              {rev.critical_count} CRIT
                            </span>
                          )}
                          {rev.high_count > 0 && (
                            <span className="text-[var(--ink-primary)]">
                              {rev.high_count} HIGH
                            </span>
                          )}
                        </div>
                      ) : rev.total_findings > 0 ? (
                        <span className="text-[var(--ink-secondary)]">
                          {rev.total_findings} finding{rev.total_findings > 1 ? "s" : ""}
                        </span>
                      ) : (
                        <span className="text-[var(--ink-muted)]">0 findings</span>
                      )}
                    </td>

                    {/* Duration */}
                    <td className="py-2.5 px-3 align-middle text-right font-mono text-[11px] text-[var(--ink-secondary)] tabular-nums">
                      {rev.execution_time_ms
                        ? `${(rev.execution_time_ms / 1000).toFixed(1)}s`
                        : "—"}
                    </td>

                    {/* Timestamp */}
                    <td className="py-2.5 px-3 align-middle text-right font-mono text-[10px] text-[var(--ink-muted)] whitespace-nowrap">
                      {formatRelativeTime(rev.created_at)}
                    </td>

                    {/* Action Arrow */}
                    <td className="py-2.5 px-3 text-center align-middle">
                      <Link
                        href={`/reviews/${rev.id}`}
                        className="inline-flex p-1 rounded-xs hover:bg-[var(--canvas)] text-[var(--ink-muted)] hover:text-[var(--ink-primary)] transition-colors"
                        title="View details"
                      >
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
