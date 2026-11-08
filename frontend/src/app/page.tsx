"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useReviewStore } from "@/store/useReviewStore";
import { StatusBadge, VerdictBadge } from "@/components/StatusBadge";
import {
  Shield,
  AlertTriangle,
  CheckCircle2,
  GitPullRequest,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { Repository, ReviewRun } from "@/lib/types";

export default function OverviewPage() {
  const {
    repositories,
    reviews,
    selectedRepoId,
    isLoading,
    error,
    loadInitialData,
    setSelectedRepoId,
  } = useReviewStore();

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const totalReviews = reviews.length;
  const criticalFindings = reviews.reduce(
    (acc: any, r: { critical_count: any }) => acc + (r.critical_count || 0),
    0,
  );
  const changesRequested = reviews.filter(
    (r) => r.verdict === "REQUEST_CHANGES",
  ).length;
  const approvedReviews = reviews.filter((r) => r.verdict === "APPROVE").length;

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Security Review Dashboard
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time multi-agent code analysis, OSV vulnerability tracking, and
            compliance audits.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedRepoId || ""}
            onChange={(e) => setSelectedRepoId(e.target.value || null)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Repositories</option>
            {repositories.map((repo: Repository) => (
              <option key={repo.id} value={repo.id}>
                {repo.full_name}
              </option>
            ))}
          </select>

          <button
            onClick={() => loadInitialData()}
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-colors"
            title="Refresh dashboard"
          >
            <RefreshCw
              className={`h-4 w-4 ${isLoading ? "animate-spin text-cyan-400" : ""}`}
            />
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">
              Total PR Reviews
            </span>
            <GitPullRequest className="h-5 w-5 text-cyan-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-white">
            {totalReviews}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Across {repositories.length} repositories
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">
              Critical Vulnerabilities
            </span>
            <AlertTriangle className="h-5 w-5 text-rose-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-rose-400">
            {criticalFindings}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Immediate action required
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">
              Changes Requested
            </span>
            <Shield className="h-5 w-5 text-amber-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-amber-400">
            {changesRequested}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Blocked by security policy
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">
              Clean Approvals
            </span>
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="mt-3 text-2xl font-bold text-emerald-400">
            {approvedReviews}
          </div>
          <div className="mt-1 text-xs text-slate-500">
            Zero policy violations
          </div>
        </div>
      </div>

      {/* Recent Reviews Table */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">
            Recent Pull Request Audits
          </h2>
          <span className="text-xs text-slate-500">
            {reviews.length} audits logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/60 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-3.5">PR / Title</th>
                <th className="px-6 py-3.5">Author</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Verdict</th>
                <th className="px-6 py-3.5">Findings</th>
                <th className="px-6 py-3.5">Execution Time</th>
                <th className="px-6 py-3.5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {reviews.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-6 py-12 text-center text-slate-500"
                  >
                    No pull request reviews found yet. Connect your GitHub App
                    and open a PR!
                  </td>
                </tr>
              ) : (
                reviews.map((r: ReviewRun) => (
                  <tr
                    key={r.id}
                    className="hover:bg-slate-900/60 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-100">
                        #{r.pull_number} {r.title || "Untitled PR"}
                      </div>
                      <div className="text-xs font-mono text-slate-500 mt-0.5">
                        SHA: {r.commit_sha.slice(0, 7)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-400">
                      @{r.pr_author}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="px-6 py-4">
                      <VerdictBadge verdict={r.verdict} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1.5 text-xs font-mono">
                        {r.critical_count > 0 && (
                          <span className="px-1.5 py-0.5 rounded bg-rose-950 text-rose-300">
                            {r.critical_count}C
                          </span>
                        )}
                        {r.high_count > 0 && (
                          <span className="px-1.5 py-0.5 rounded bg-orange-950 text-orange-300">
                            {r.high_count}H
                          </span>
                        )}
                        {r.medium_count > 0 && (
                          <span className="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300">
                            {r.medium_count}M
                          </span>
                        )}
                        {r.total_findings === 0 && (
                          <span className="text-emerald-400 font-medium">
                            0 issues
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {r.execution_time_ms
                        ? `${(r.execution_time_ms / 1000).toFixed(1)}s`
                        : "-"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/reviews/${r.id}`}
                        className="inline-flex items-center gap-1 text-xs font-medium text-cyan-400 hover:text-cyan-300 transition-colors"
                      >
                        Inspect
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
