"use client";

import React from "react";
import Link from "next/link";
import { Plus, RefreshCw, Menu } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useReviewStore } from "@/store/useReviewStore";
import { useSidebar } from "./SidebarContext";

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
  const { toggleSidebar } = useSidebar();

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    } else {
      loadInitialData();
    }
  };

  return (
    <header className="sticky top-0 z-20 bg-[var(--surface)] border-b border-[var(--hairline)] px-3 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3">
      {/* Left: Mobile Menu Button + Breadcrumb */}
      <div className="flex items-center gap-2 text-xs font-mono">
        {/* Mobile Hamburger Drawer Trigger */}
        <button
          type="button"
          onClick={toggleSidebar}
          className="p-1.5 rounded-sm border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors lg:hidden flex-shrink-0"
          aria-label="Open navigation menu"
          title="Open menu"
        >
          <Menu className="w-4 h-4" />
        </button>

        <Link
          href="/"
          className="text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
        >
          workspace
        </Link>
        <span className="text-[var(--ink-muted)]">/</span>
        <span className="text-[var(--ink-secondary)] hidden sm:inline">
          pr-sentinel
        </span>
        <span className="text-[var(--ink-muted)] hidden sm:inline">/</span>
        <span className="text-[var(--ink-primary)] font-medium">reviews</span>
      </div>

      {/* Center Controls: Segmented Filter Controls */}
      <div className="order-3 sm:order-2 w-full sm:w-auto overflow-x-auto flex justify-start sm:justify-center py-1 sm:py-0">
        <div className="inline-flex p-0.5 border border-[var(--hairline)] bg-[var(--canvas)] rounded-sm text-[11px] font-mono flex-shrink-0">
          <button
            type="button"
            onClick={() => onFilterChange && onFilterChange("ALL")}
            className={`px-2.5 py-1 rounded-xs transition-colors ${
              currentFilter === "ALL"
                ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
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

      {/* Right Actions: Sync, Theme toggle, and ONE solid-ink Deploy/Connect button */}
      <div className="order-2 sm:order-3 flex items-center gap-2 flex-shrink-0">
        {/* Ghost sync button */}
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
          <span className="hidden md:inline">SYNC</span>
        </button>

        {/* Theme Toggle (Paper / Carbon) */}
        <ThemeToggle />

        {/* ONE Solid-Ink Primary Action Button */}
        <Link
          href="/repositories"
          className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all"
        >
          <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
          <span className="hidden sm:inline">CONNECT REPO</span>
          <span className="sm:hidden">REPO</span>
        </Link>
      </div>
    </header>
  );
}
