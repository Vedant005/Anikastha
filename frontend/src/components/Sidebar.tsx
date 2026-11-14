"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  GitPullRequest,
  FolderGit2,
  Sliders,
  Terminal,
  Search,
  ChevronDown,
  X,
} from "lucide-react";
import { InkGlyph } from "./InkGlyph";
import { useReviewStore } from "@/store/useReviewStore";
import { useSidebar } from "./SidebarContext";

export function Sidebar() {
  const pathname = usePathname();
  const { repositories, reviews, selectedRepoId, setSelectedRepoId } =
    useReviewStore();
  const { isOpen, closeSidebar } = useSidebar();
  const [searchQuery, setSearchQuery] = useState("");

  const navItems = [
    {
      label: "Reviews",
      href: "/",
      icon: GitPullRequest,
      active: pathname === "/" || pathname.startsWith("/reviews"),
      badge: "LIVE",
    },
    {
      label: "Repositories",
      href: "/repositories",
      icon: FolderGit2,
      active: pathname.startsWith("/repositories"),
    },
    {
      label: "Security Policies",
      href: "/repositories",
      icon: Sliders,
      active: false,
    },
    {
      label: "Audit Logs",
      href: "#audit-logs",
      icon: Terminal,
      active: false,
    },
  ];

  // Dynamic quota usage
  const totalScans = reviews ? reviews.length : 0;
  const maxQuota = 600;
  const quotaPercent = Math.min(100, Math.round((totalScans / maxQuota) * 100));

  const sidebarContent = (
    <div className="flex flex-col h-full w-full justify-between select-none">
      {/* Scrollable Top & Middle Section */}
      <div className="flex-1 overflow-y-auto min-h-0 flex flex-col">
        {/* Workspace Switcher */}
        <div className="p-3.5 border-b border-[var(--hairline)] flex-shrink-0">
          <div className="flex items-center justify-between p-1.5 rounded-sm hover:bg-[var(--surface-subtle)] transition-colors cursor-pointer">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-6 h-6 rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] flex items-center justify-center font-mono font-bold text-xs flex-shrink-0">
                A
              </div>
              <div className="min-w-0 flex flex-col">
                <span className="text-xs font-semibold tracking-tight truncate leading-tight">
                  ANIKASTHA
                </span>
                <span className="text-[10px] font-mono text-[var(--ink-muted)] truncate">
                  workspace
                </span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <ChevronDown className="w-3.5 h-3.5 text-[var(--ink-muted)] flex-shrink-0" />
              {/* Mobile Close Button */}
              <button
                type="button"
                onClick={closeSidebar}
                className="p-1 rounded-sm text-[var(--ink-muted)] hover:text-[var(--ink-primary)] lg:hidden ml-1"
                aria-label="Close sidebar"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Quick Search */}
          <div className="mt-3 relative">
            <Search className="w-3.5 h-3.5 text-[var(--ink-muted)] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Find PR, SHA or CVE..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-8 py-1.5 text-[11px] font-mono bg-[var(--canvas)] border border-[var(--hairline)] rounded-sm text-[var(--ink-primary)] placeholder-[var(--ink-muted)] focus:outline-none focus:border-[var(--ink-primary)] transition-colors"
            />
            <kbd className="absolute right-2 top-1/2 -translate-y-1/2 text-[9px] font-mono px-1 py-0.2 rounded border border-[var(--hairline)] text-[var(--ink-muted)] bg-[var(--surface)]">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Navigation Group */}
        <div className="py-2.5 flex-shrink-0">
          <div className="px-3.5 pb-1.5 text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-muted)] uppercase">
            Platform
          </div>
          <nav className="flex flex-col space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  onClick={() => closeSidebar()}
                  className={`group relative flex items-center justify-between px-3.5 py-1.5 text-xs transition-colors ${
                    item.active
                      ? "text-[var(--ink-primary)] font-medium bg-[var(--canvas)]"
                      : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:bg-[var(--surface-subtle)]"
                  }`}
                >
                  {/* Left hairline indicator for active page */}
                  {item.active && (
                    <span className="absolute left-0 top-0 bottom-0 w-[2px] bg-[var(--ink-primary)]" />
                  )}
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon className="w-3.5 h-3.5 flex-shrink-0 opacity-75 group-hover:opacity-100" />
                    <span className="truncate">{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[9px] font-mono px-1 py-0.2 rounded-xs border border-[var(--hairline)] text-[var(--ink-muted)]">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Repositories / Environments Group */}
        <div className="py-2 border-t border-[var(--hairline)]">
          <div className="px-3.5 pb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-muted)] uppercase">
              Monitored Repos
            </span>
            <span className="text-[10px] font-mono text-[var(--ink-muted)]">
              {repositories.length}
            </span>
          </div>

          <div className="flex flex-col space-y-0.5">
            {/* All Filter Option */}
            <button
              onClick={() => {
                setSelectedRepoId(null);
                closeSidebar();
              }}
              className={`w-full text-left px-3.5 py-1.5 text-xs flex items-center justify-between transition-colors ${
                selectedRepoId === null
                  ? "bg-[var(--canvas)] text-[var(--ink-primary)] font-medium"
                  : "text-[var(--ink-secondary)] hover:bg-[var(--surface-subtle)]"
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <InkGlyph type="ready" size="sm" />
                <span className="truncate">All Repositories</span>
              </div>
            </button>

            {repositories.slice(0, 10).map((repo) => {
              const isSelected = selectedRepoId === repo.id;
              const shortName = repo.full_name.split("/")[1] || repo.full_name;
              return (
                <button
                  key={repo.id}
                  onClick={() => {
                    setSelectedRepoId(repo.id);
                    closeSidebar();
                  }}
                  className={`w-full text-left px-3.5 py-1.5 text-xs flex items-center justify-between transition-colors ${
                    isSelected
                      ? "bg-[var(--canvas)] text-[var(--ink-primary)] font-medium"
                      : "text-[var(--ink-secondary)] hover:bg-[var(--surface-subtle)]"
                  }`}
                  title={repo.full_name}
                >
                  <div className="flex items-center gap-2 truncate">
                    <InkGlyph
                      type={repo.is_active ? "ready" : "canceled"}
                      size="sm"
                    />
                    <span className="font-mono text-[11px] truncate">
                      {shortName}
                    </span>
                  </div>
                </button>
              );
            })}

            {repositories.length === 0 && (
              <div className="px-3.5 py-2 text-[11px] font-mono text-[var(--ink-muted)] italic">
                No repositories added
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="sticky bottom-0 w-full mt-auto flex-shrink-0 flex flex-col border-t border-[var(--hairline)] bg-[var(--surface)] z-10">
        {/* <div className="p-3.5 bg-[var(--surface-subtle)] border-b border-[var(--hairline)] w-full">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-[var(--ink-secondary)]">Review Quota</span>
            <span className="font-medium text-[var(--ink-primary)] tabular-nums">
              {totalScans} / {maxQuota}
            </span>
          </div>

            
          <div className="mt-2 w-full h-1.5 bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs overflow-hidden">
            <div
              className="h-full bg-[var(--ink-primary)] transition-all duration-300"
              style={{ width: `${Math.max(2, quotaPercent)}%` }}
            />
          </div>

          <div className="mt-1.5 flex items-center justify-between text-[10px] font-mono text-[var(--ink-muted)]">
            <span>{quotaPercent}% allocated</span>
            <span>Resets in 18d</span>
          </div>
        </div> */}

        {/* User Profile Row */}
        <div className="p-3 flex items-center justify-between w-full">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-sm border border-[var(--hairline)] bg-[var(--canvas)] flex items-center justify-center font-mono font-semibold text-xs text-[var(--ink-primary)] flex-shrink-0">
              VD
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-medium truncate text-[var(--ink-primary)]">
                vedant
              </span>
              {/* <span className="text-[10px] font-mono text-[var(--ink-muted)] truncate">
                sec-engineer &bull; pro
              </span> */}
            </div>
          </div>

          <span
            className="w-2 h-2 rounded-full bg-[var(--ink-primary)] flex-shrink-0"
            title="Agent Daemon Active"
          />
        </div>
      </div>
    </div>
  );

  return (
    <>
      <aside className="hidden lg:flex w-60 min-w-[240px] max-w-[240px] flex-shrink-0 flex-col justify-between bg-[var(--surface)] border-r border-[var(--hairline)] h-screen sticky top-0 text-[var(--ink-primary)] z-30">
        {sidebarContent}
      </aside>

      {isOpen && (
        <div className="lg:hidden">
          <div
            onClick={closeSidebar}
            className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 transition-opacity animate-in fade-in"
            aria-hidden="true"
          />

          <aside className="fixed inset-y-0 left-0 z-50 w-64 max-w-[85vw] bg-[var(--surface)] border-r border-[var(--hairline)] flex flex-col justify-between shadow-2xl animate-in slide-in-from-left duration-200">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
