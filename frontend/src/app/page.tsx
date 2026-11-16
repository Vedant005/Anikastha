"use client";

import { useEffect, useState, useMemo } from "react";
import { useReviewStore } from "@/store/useReviewStore";
import { useAuthStore } from "@/store/useAuthStore";
import { LandingPage } from "@/components/LandingPage";
import { Header, FilterStatus } from "@/components/Header";
import { HeroCard } from "@/components/HeroCard";
import { ReviewsTable } from "@/components/ReviewsTable";
import { BottomSplit } from "@/components/BottomSplit";
import { UserAuthControl } from "@/components/UserAuthControl";
import { DEMO_REPOSITORIES, DEMO_REVIEWS } from "@/lib/demoData";
import { AlertCircle, ArrowLeft } from "lucide-react";

export default function RootPage() {
  const { token, user, showConsoleDemo, setShowConsoleDemo } = useAuthStore();
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
    // Only load repos and reviews if authenticated
    if (token) {
      loadInitialData({ silent: true });
    } else {
      useReviewStore.setState({
        repositories: [],
        reviews: [],
        selectedRepoId: null,
      });
    }
  }, [token, loadInitialData]);

  // Active data: in demo console mode use DEMO data, otherwise use authenticated store data
  const isDemo = !token && showConsoleDemo;
  const activeRepos = useMemo(
    () => (isDemo ? DEMO_REPOSITORIES : repositories),
    [isDemo, repositories],
  );
  const activeReviews = useMemo(
    () => (isDemo ? DEMO_REVIEWS : reviews),
    [isDemo, reviews],
  );

  // Find latest review for Hero card
  const latestReview = useMemo(() => {
    if (!activeReviews || activeReviews.length === 0) return null;
    return activeReviews[0];
  }, [activeReviews]);

  // Find repo name for latest review
  const latestRepoName = useMemo(() => {
    if (!latestReview) return undefined;
    const r = activeRepos.find((x) => x.id === latestReview.repository_id);
    return r ? r.full_name : undefined;
  }, [latestReview, activeRepos]);

  // Find latest failed or changes requested review for advisory log
  const failedReview = useMemo(() => {
    return (
      activeReviews.find(
        (r) => r.status === "FAILED" || r.verdict === "REQUEST_CHANGES",
      ) || null
    );
  }, [activeReviews]);

  // Filtered reviews for the table
  const filteredReviews = useMemo(() => {
    if (!activeReviews) return [];
    switch (filter) {
      case "REQUEST_CHANGES":
        return activeReviews.filter(
          (r) => r.verdict === "REQUEST_CHANGES" || r.status === "FAILED",
        );
      case "APPROVE":
        return activeReviews.filter((r) => r.verdict === "APPROVE");
      case "PROCESSING":
        return activeReviews.filter(
          (r) => r.status === "PROCESSING" || r.status === "PENDING",
        );
      case "ALL":
      default:
        return activeReviews;
    }
  }, [activeReviews, filter]);

  // RULE OF HOOKS: All hooks called above unconditionally.
  // DEFAULT EXPERIENCE: If user is not signed in and hasn't toggled demo console, show LANDING PAGE!
  if (!token && !showConsoleDemo) {
    return <LandingPage onOpenConsole={() => setShowConsoleDemo(true)} />;
  }

  return (
    <div className="flex flex-col flex-1">
      {/* Top Header Bar with Segmented Control & Actions */}
      <Header
        currentFilter={filter}
        onFilterChange={setFilter}
        onRefresh={isDemo ? undefined : loadInitialData}
        isRefreshing={isLoading}
      />

      {/* If viewing in unauthenticated Demo Mode, show a return banner */}
      {isDemo && (
        <div className="bg-[var(--surface)] border-b border-[var(--hairline)] px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 text-[var(--ink-secondary)]">
            <span className="w-2 h-2 rounded-full bg-[var(--ink-primary)]"></span>
            <span>Console Demo Mode &bull; Sign in with GitHub to audit your live repositories</span>
          </div>
          <div className="flex items-center gap-3">
            <UserAuthControl variant="header" />
            <button
              type="button"
              onClick={() => setShowConsoleDemo(false)}
              className="inline-flex items-center gap-1.5 text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:underline font-semibold cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Return to Landing Page</span>
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <main className="p-4 sm:p-6 lg:p-8 space-y-6 flex-1 max-w-[1440px] w-full mx-auto flex flex-col justify-between">
        {/* Error Alert if any */}
        {error && !isDemo && (
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
        <HeroCard latestReview={latestReview} repoName={latestRepoName} />

        {/* 2. DENSE HAIRLINE-DIVIDED REVIEWS TABLE */}
        <ReviewsTable
          reviews={filteredReviews}
          repositories={activeRepos}
          isLoading={isLoading}
        />

        {/* 3. SPLIT ROW: LAST SECURITY ADVISORY (LOG EXCERPT) + 14-DAY STEPPED BAR CHART */}
        <BottomSplit
          failedReview={failedReview}
          reviews={activeReviews}
          repositories={activeRepos}
        />
      </main>
    </div>
  );
}
