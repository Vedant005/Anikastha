"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  GitPullRequest,
  FolderGit2,
  Sliders,
  Terminal,
  Activity,
  Search,
  ChevronDown,
  Layers,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { InkGlyph } from "./InkGlyph";
import { useReviewStore } from "@/store/useReviewStore";

export function Sidebar() {
  const pathname = usePathname();
  const { repositories, selectedRepoId, setSelectedRepoId } = useReviewStore();
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

  return (
    <aside className="w-full lg:w-60 lg:min-w-[240px] lg:max-w-[240px] flex-shrink-0 flex flex-col justify-between bg-[var(--surface)] border-r border-[var(--hairline)] min-h-screen text-[var(--ink-primary)] select-none">
      {/* Top Section */}
      <div className="flex flex-col">
        {/* Workspace Switcher */}
        <div className="p-3.5 border-b border-[var(--hairline)]">
          <div className="flex items-center justify-between p-1.5 rounded-sm hover:bg-[var(--surface-subtle)] transition-colors cursor-pointer">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-6 h-6 rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] flex items-center justify-center font-mono font-bold text-xs flex-shrink-0">
                PS
              </div>
              <div className="min-w-0 flex flex-col">
                <span className="text-xs font-semibold tracking-tight truncate leading-tight">
                  PR-Sentinel
                </span>
                <span className="text-[10px] font-mono text-[var(--ink-muted)] truncate">
                  workspace / sec-ops
                </span>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[var(--ink-muted)] flex-shrink-0 ml-1" />
          </div>

          {/* Quick Cmd-K Search */}
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
        <div className="py-2.5">
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
              onClick={() => setSelectedRepoId(null)}
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

            {repositories.slice(0, 6).map((repo) => {
              const isSelected = selectedRepoId === repo.id;
              const shortName = repo.full_name.split("/")[1] || repo.full_name;
              return (
                <button
                  key={repo.id}
                  onClick={() => setSelectedRepoId(repo.id)}
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

      {/* Bottom Section */}
      <div className="flex flex-col border-t border-[var(--hairline)]">
        {/* Pinned Scans / Build-Minutes Usage Meter */}
        <div className="p-3.5 bg-[var(--surface-subtle)] border-b border-[var(--hairline)]">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-[var(--ink-secondary)]">Review Quota</span>
            <span className="font-medium text-[var(--ink-primary)]">
              412 / 600
            </span>
          </div>

          {/* Stepped ink meter */}
          <div className="mt-2 w-full h-1.5 bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs overflow-hidden">
            <div
              className="h-full bg-[var(--ink-primary)]"
              style={{ width: "68.6%" }}
            />
          </div>

          <div className="mt-1.5 flex items-center justify-between text-[10px] font-mono text-[var(--ink-muted)]">
            <span>68% allocated</span>
            <span>Resets in 18d</span>
          </div>
        </div>

        {/* User Profile Row */}
        <div className="p-3 flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-sm border border-[var(--hairline)] bg-[var(--canvas)] flex items-center justify-center font-mono font-semibold text-xs text-[var(--ink-primary)]">
              VD
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-xs font-medium truncate text-[var(--ink-primary)]">
                vedant
              </span>
              <span className="text-[10px] font-mono text-[var(--ink-muted)] truncate">
                sec-engineer &bull; pro
              </span>
            </div>
          </div>

          <span
            className="w-2 h-2 rounded-full bg-[var(--ink-primary)]"
            title="Agent Daemon Active"
          />
        </div>
      </div>
    </aside>
  );
}
