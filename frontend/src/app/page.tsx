"use client";

import { useEffect, useState, useMemo } from "react";
import { useReviewStore } from "@/store/useReviewStore";
import { Header, FilterStatus } from "@/components/Header";
import { HeroCard } from "@/components/HeroCard";
import { ReviewsTable } from "@/components/ReviewsTable";
import { BottomSplit } from "@/components/BottomSplit";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function OverviewPage() {
  const {
    repositories,
    reviews,
    selectedRepoId,
    isLoading,
    error,
    loadInitialData,
  } = useReviewStore();

  const [filter, setFilter] = useState<FilterStatus>("ALL");

  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // Find latest review for Hero card
  const latestReview = useMemo(() => {
    if (!reviews || reviews.length === 0) return null;
    return reviews[0];
  }, [reviews]);

  // Find repo name for latest review
  const latestRepoName = useMemo(() => {
    if (!latestReview) return undefined;
    const r = repositories.find((x) => x.id === latestReview.repository_id);
    return r ? r.full_name : undefined;
  }, [latestReview, repositories]);

  // Find latest failed or changes requested review for advisory log
  const failedReview = useMemo(() => {
    return (
      reviews.find(
        (r) => r.status === "FAILED" || r.verdict === "REQUEST_CHANGES"
      ) || null
    );
  }, [reviews]);

  // Filtered reviews for the table
  const filteredReviews = useMemo(() => {
    if (!reviews) return [];
    switch (filter) {
      case "REQUEST_CHANGES":
        return reviews.filter(
          (r) => r.verdict === "REQUEST_CHANGES" || r.status === "FAILED"
        );
      case "APPROVE":
        return reviews.filter((r) => r.verdict === "APPROVE");
      case "PROCESSING":
        return reviews.filter(
          (r) => r.status === "PROCESSING" || r.status === "PENDING"
        );
      case "ALL":
      default:
        return reviews;
    }
  }, [reviews, filter]);

  return (
    <div className="flex flex-col flex-1">
      {/* Top Header Bar with Segmented Control & Actions */}
      <Header
        currentFilter={filter}
        onFilterChange={setFilter}
        onRefresh={loadInitialData}
        isRefreshing={isLoading}
      />

      {/* Main Content Area */}
      <main className="p-4 sm:p-6 lg:p-8 space-y-6 flex-1 max-w-[1440px] w-full mx-auto">
        {/* Error Alert if any */}
        {error && (
          <div className="p-3 border border-[var(--signal-red-border)] bg-[var(--signal-red-bg)] text-[var(--signal-red)] rounded-sm text-xs font-mono flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => loadInitialData()}
              className="text-[10px] underline hover:no-underline font-semibold"
            >
              Retry
            </button>
          </div>
        )}

        {/* 1. CURRENT PRODUCTION / LATEST SECURITY AUDIT HERO CARD */}
        <HeroCard
          latestReview={latestReview}
          repoName={latestRepoName}
        />

        {/* 2. DENSE HAIRLINE-DIVIDED REVIEWS TABLE */}
        <ReviewsTable
          reviews={filteredReviews}
          repositories={repositories}
          isLoading={isLoading}
        />

        {/* 3. SPLIT ROW: LAST SECURITY ADVISORY (LOG EXCERPT) + 14-DAY STEPPED BAR CHART */}
        <BottomSplit
          failedReview={failedReview}
          reviews={reviews}
        />
      </main>
    </div>
  );
}
