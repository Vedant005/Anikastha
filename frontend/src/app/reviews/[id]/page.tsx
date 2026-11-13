"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import { fetchReviewById, rerunReview, API_BASE } from "@/lib/api";
import { ReviewRun } from "@/lib/types";
import { StatusBadge, VerdictBadge } from "@/components/StatusBadge";
import { InkGlyph } from "@/components/InkGlyph";
import { FindingCard } from "@/components/FindingCard";
import {
  ArrowLeft,
  RefreshCw,
  GitCommit,
  User,
  Calendar,
  Clock,
  ExternalLink,
  Shield,
  Layers,
} from "lucide-react";

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
    if (
      !review ||
      (review.status !== "PENDING" && review.status !== "PROCESSING")
    ) {
      return;
    }

    const eventSource = new EventSource(
      `${API_BASE}/reviews/${reviewId}/events`
    );

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
        <RefreshCw className="h-6 w-6 text-[var(--ink-secondary)] animate-spin mx-auto mb-3" />
        <p className="text-xs font-mono text-[var(--ink-muted)]">
          Querying security audit details from ledger...
        </p>
      </div>
    );
  }

  if (error || !review) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Dashboard
        </Link>
        <div className="p-4 rounded-sm bg-[var(--signal-red-bg)] border border-[var(--signal-red-border)] text-[var(--signal-red)] text-xs font-mono">
          {error || "Review record not found."}
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
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-[1440px] w-full mx-auto">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[var(--hairline)]">
        <div className="flex items-center gap-2 text-xs font-mono">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back
          </Link>
          <span className="text-[var(--ink-muted)]">/</span>
          <span className="text-[var(--ink-primary)] font-medium">
            Review #{review.pull_number}
          </span>
        </div>

        <button
          onClick={handleRerun}
          disabled={isRerunning || review.status === "PROCESSING"}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-sm bg-[var(--surface)] border border-[var(--hairline)] hover:border-[var(--ink-primary)] text-[var(--ink-primary)] text-xs font-mono font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${isRerunning ? "animate-spin" : ""}`}
          />
          {isRerunning ? "Re-queuing..." : "RERUN AUDIT"}
        </button>
      </div>

      {/* Review Summary Hero Card */}
      <div className="border border-[var(--hairline)] bg-[var(--surface)] p-5 sm:p-6 rounded-sm dot-grain-texture">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <InkGlyph
                status={review.status}
                verdict={review.verdict}
                size="md"
              />
              <h1 className="text-base sm:text-xl font-bold tracking-tight text-[var(--ink-primary)] truncate">
                PR #{review.pull_number}: {review.title || "Untitled Pull Request"}
              </h1>
              <StatusBadge status={review.status} />
              <VerdictBadge verdict={review.verdict} />
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--ink-secondary)] mt-3 font-mono">
              <span className="flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 opacity-60" />
                @{review.pr_author}
              </span>
              <span className="flex items-center gap-1.5">
                <GitCommit className="w-3.5 h-3.5 opacity-60" />
                SHA: {review.commit_sha.slice(0, 7)}
              </span>
              <span className="flex items-center gap-1.5 text-[var(--ink-muted)]">
                <Calendar className="w-3.5 h-3.5 opacity-60" />
                {new Date(review.created_at).toLocaleString()}
              </span>
              {review.execution_time_ms && (
                <span className="flex items-center gap-1 text-[var(--ink-primary)] font-medium">
                  <Clock className="w-3.5 h-3.5 opacity-60" />
                  {(review.execution_time_ms / 1000).toFixed(2)}s
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Severity Counters Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-[var(--hairline)]">
          <div className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-center font-mono">
            <div className="text-[10px] uppercase text-[var(--ink-muted)]">
              Critical
            </div>
            <div
              className={`text-xl font-bold mt-0.5 ${
                review.critical_count > 0 ? "text-[var(--signal-red)]" : "text-[var(--ink-primary)]"
              }`}
            >
              {review.critical_count}
            </div>
          </div>
          <div className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-center font-mono">
            <div className="text-[10px] uppercase text-[var(--ink-muted)]">
              High
            </div>
            <div className="text-xl font-bold text-[var(--ink-primary)] mt-0.5">
              {review.high_count}
            </div>
          </div>
          <div className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-center font-mono">
            <div className="text-[10px] uppercase text-[var(--ink-muted)]">
              Medium
            </div>
            <div className="text-xl font-bold text-[var(--ink-secondary)] mt-0.5">
              {review.medium_count}
            </div>
          </div>
          <div className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-center font-mono">
            <div className="text-[10px] uppercase text-[var(--ink-muted)]">
              Low / Info
            </div>
            <div className="text-xl font-bold text-[var(--ink-muted)] mt-0.5">
              {review.low_count}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs & Findings Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--hairline)] pb-2.5">
          <div className="flex items-center gap-1 font-mono text-xs">
            {["all", "critical", "high", "medium", "low"].map((tab) => {
              const count =
                tab === "all"
                  ? findings.length
                  : findings.filter(
                      (f) => f.severity.toLowerCase() === tab.toLowerCase()
                    ).length;

              const isSelected = activeTab === tab;

              return (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-1 rounded-xs transition-colors capitalize ${
                    isSelected
                      ? "bg-[var(--ink-primary)] text-[var(--canvas)] font-medium"
                      : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:bg-[var(--surface-subtle)]"
                  }`}
                >
                  {tab} ({count})
                </button>
              );
            })}
          </div>
        </div>

        {filteredFindings.length === 0 ? (
          <div className="p-12 text-center bg-[var(--surface)] border border-[var(--hairline)] rounded-sm">
            <p className="text-xs font-mono text-[var(--ink-muted)]">
              No security findings recorded under the &apos;{activeTab}&apos; filter.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {filteredFindings.map((f) => (
              <FindingCard key={f.id} finding={f} />
            ))}
          </div>
        )}
      </div>

      {/* Markdown GitHub Review Body Preview */}
      {review.summary_markdown && (
        <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm p-5 sm:p-6">
          <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-[var(--ink-primary)] mb-3">
            GitHub Review Body &bull; Published Output
          </h3>
          <pre className="p-4 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-xs font-mono text-[var(--ink-primary)] overflow-x-auto whitespace-pre-wrap leading-relaxed select-text">
            {review.summary_markdown}
          </pre>
        </div>
      )}
    </div>
  );
}
