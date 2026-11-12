"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { fetchReviewById, rerunReview, API_BASE } from "@/lib/api";
import { ReviewRun } from "@/lib/types";
import { StatusBadge, VerdictBadge } from "@/components/StatusBadge";
import { FindingCard } from "@/components/FindingCard";
import { ArrowLeft, RefreshCw, GitCommit, User, Calendar, ExternalLink } from "lucide-react";

export default function ReviewDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const reviewId = resolvedParams.id;

  const [review, setReview] = useState<ReviewRun | null>(null);
  const [activeTab, setActiveTab] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isRerunning, setIsRerunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial review data
  useEffect(() => {
    fetchReviewById(reviewId)
      .then((data) => {
        setReview(data);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setIsLoading(false);
      });
  }, [reviewId]);

  // Connect to SSE stream if status is PENDING or PROCESSING
  useEffect(() => {
    if (!review || (review.status !== "PENDING" && review.status !== "PROCESSING")) {
      return;
    }

    const eventSource = new EventSource(`${API_BASE}/reviews/${reviewId}/events`);

    eventSource.onmessage = (event) => {
      try {
        const update = JSON.parse(event.data);
        if (update.status) {
          setReview((prev) => (prev ? { ...prev, ...update } : null));
          if (update.status === "COMPLETED" || update.status === "FAILED") {
            eventSource.close();
            // Refetch full review to get populated findings list
            fetchReviewById(reviewId).then((full) => setReview(full));
          }
        }
      } catch (err) {
        console.error("SSE parse error", err);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [reviewId, review?.status]);

  const handleRerun = async () => {
    setIsRerunning(true);
    try {
      await rerunReview(reviewId);
      const updated = await fetchReviewById(reviewId);
      setReview(updated);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsRerunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="py-24 text-center">
        <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto mb-4" />
        <p className="text-sm text-slate-400">Loading security audit details...</p>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="py-12 space-y-4">
        <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-cyan-400 hover:underline">
          <ArrowLeft className="h-4 w-4" /> Back to Reviews
        </Link>
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error || "Review not found."}
        </div>
      </div>
    );
  }

  const findings = review.findings || [];
  const filteredFindings = findings.filter((f) => {
    if (activeTab === "all") return true;
    return f.severity.toLowerCase() === activeTab.toLowerCase();
  });

  return (
    <div className="space-y-8">
      {/* Back button & Rerun */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Link>

        <button
          onClick={handleRerun}
          disabled={isRerunning || review.status === "PROCESSING"}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 text-xs font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRerunning ? "animate-spin" : ""}`} />
          {isRerunning ? "Re-queuing..." : "Rerun Audit"}
        </button>
      </div>

      {/* Audit Header Card */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">
                Pull Request #{review.pull_number}: {review.title || "Untitled PR"}
              </h1>
              <StatusBadge status={review.status} />
              <VerdictBadge verdict={review.verdict} />
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-3 font-mono">
              <span className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5 text-slate-500" />
                @{review.pr_author}
              </span>
              <span className="flex items-center gap-1.5">
                <GitCommit className="h-3.5 w-3.5 text-slate-500" />
                SHA: {review.commit_sha.slice(0, 7)}
              </span>
              <span className="flex items-center gap-1.5">
                <Calendar className="h-3.5 w-3.5 text-slate-500" />
                {new Date(review.created_at).toLocaleString()}
              </span>
              {review.execution_time_ms && (
                <span className="text-cyan-400">
                  Time: {(review.execution_time_ms / 1000).toFixed(1)}s
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Severity counts pill row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-6 border-t border-slate-800/80">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
            <div className="text-xs text-slate-400">Critical</div>
            <div className="text-xl font-bold text-rose-400 mt-0.5">{review.critical_count}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
            <div className="text-xs text-slate-400">High</div>
            <div className="text-xl font-bold text-orange-400 mt-0.5">{review.high_count}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
            <div className="text-xs text-slate-400">Medium</div>
            <div className="text-xl font-bold text-amber-300 mt-0.5">{review.medium_count}</div>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-center">
            <div className="text-xs text-slate-400">Low / Info</div>
            <div className="text-xl font-bold text-blue-400 mt-0.5">{review.low_count}</div>
          </div>
        </div>
      </div>

      {/* Tabs & Findings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            {["all", "critical", "high", "medium", "low"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                  activeTab === tab
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-800"
                    : "text-slate-400 hover:text-white bg-slate-900/50"
                }`}
              >
                {tab} ({tab === "all" ? findings.length : findings.filter((f) => f.severity.toLowerCase() === tab).length})
              </button>
            ))}
          </div>
        </div>

        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center bg-slate-900/20 border border-slate-800 rounded-xl">
            <p className="text-sm text-slate-400">No findings matching the selected filter.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredFindings.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </div>
        )}
      </div>

      {/* Markdown Executive Summary */}
      {review.summary_markdown && (
        <div className="bg-slate-900/30 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
            GitHub Review Body Preview
          </h3>
          <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {review.summary_markdown}
          </pre>
        </div>
      )}
    </div>
  );
}
