"use client";

import React from "react";
import Link from "next/link";
import { SlidersHorizontal, Plus, RefreshCw } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useReviewStore } from "@/store/useReviewStore";

export type FilterStatus = "ALL" | "REQUEST_CHANGES" | "APPROVE" | "PROCESSING";

interface HeaderProps {
  currentFilter?: FilterStatus;
  onFilterChange?: (filter: FilterStatus) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({
  currentFilter = "ALL",
  onFilterChange,
  onRefresh,
  isRefreshing = false,
}: HeaderProps) {
  const { loadInitialData, isLoading } = useReviewStore();

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      loadInitialData();
    }
  };

  return (
    <header className="sticky top-0 z-30 bg-[var(--surface)] border-b border-[var(--hairline)] px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3">
      {/* Breadcrumb / Section Header */}
      <div className="flex items-center gap-2 text-xs font-mono">
        <Link
          href="/"
          className="text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
        >
          workspace
        </Link>
        <span className="text-[var(--ink-muted)]">/</span>
        <span className="text-[var(--ink-secondary)]">pr-sentinel</span>
        <span className="text-[var(--ink-muted)]">/</span>
        <span className="text-[var(--ink-primary)] font-medium">reviews</span>
      </div>

      {/* Center Controls: Segmented Filter Controls */}
      <div className="flex items-center gap-2">
        <div className="inline-flex p-0.5 border border-[var(--hairline)] bg-[var(--canvas)] rounded-sm text-[11px] font-mono">
          <button
            type="button"
            onClick={() => onFilterChange && onFilterChange("ALL")}
            className={`px-2.5 py-1 rounded-xs transition-colors ${
              currentFilter === "ALL"
                ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium shadow-none border border-[var(--hairline)]"
                : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => onFilterChange && onFilterChange("REQUEST_CHANGES")}
            className={`px-2.5 py-1 rounded-xs transition-colors flex items-center gap-1.5 ${
              currentFilter === "REQUEST_CHANGES"
                ? "bg-[var(--surface)] text-[var(--signal-red)] font-medium border border-[var(--hairline)]"
                : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--signal-red)]" />
            Changes Requested
          </button>
          <button
            type="button"
            onClick={() => onFilterChange && onFilterChange("APPROVE")}
            className={`px-2.5 py-1 rounded-xs transition-colors ${
              currentFilter === "APPROVE"
                ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
                : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
            }`}
          >
            Approved
          </button>
          <button
            type="button"
            onClick={() => onFilterChange && onFilterChange("PROCESSING")}
            className={`px-2.5 py-1 rounded-xs transition-colors ${
              currentFilter === "PROCESSING"
                ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
                : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
            }`}
          >
            Processing
          </button>
        </div>
      </div>

      {/* Right Actions: Filter button, Theme toggle, and ONE solid-ink Deploy/Audit button */}
      <div className="flex items-center gap-2">
        {/* Ghost filter button */}
        <button
          type="button"
          onClick={handleRefresh}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-mono border border-[var(--hairline)] rounded-sm bg-transparent text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
          title="Refresh Reviews"
        >
          <RefreshCw
            className={`w-3.5 h-3.5 ${
              isRefreshing || isLoading ? "animate-spin text-[var(--ink-primary)]" : ""
            }`}
          />
          <span className="hidden sm:inline">SYNC</span>
        </button>

        {/* Theme Toggle (Paper / Carbon) */}
        <ThemeToggle />

        {/* ONE Solid-Ink Primary Action Button */}
        <Link
          href="/repositories"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          <span>CONNECT REPO</span>
        </Link>
      </div>
    </header>
  );
}
