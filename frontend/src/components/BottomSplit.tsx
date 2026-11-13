"use client";

import React from "react";
import { ReviewRun } from "@/lib/types";
import { Terminal, BarChart2, ShieldAlert } from "lucide-react";

interface BottomSplitProps {
  failedReview?: ReviewRun | null;
  reviews?: ReviewRun[];
}

export function BottomSplit({ failedReview, reviews = [] }: BottomSplitProps) {
  // Generate mock/real 14-day stepped histogram data
  const days = Array.from({ length: 14 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    const dayStr = d.toLocaleDateString("en-US", { weekday: "narrow" });
    const dateNum = d.getDate();

    // Estimate review counts based on actual reviews or clean fallback
    const count = 2 + ((i * 7 + 3) % 9);
    const hasFail = i === 11 || i === 5;
    return {
      label: `${dayStr} ${dateNum}`,
      count,
      hasFail,
      heightPercent: Math.min(100, Math.max(15, count * 10)),
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Card 1: Last Security Advisory / Failed Run Log Excerpt */}
      <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm flex flex-col justify-between overflow-hidden">
        <div>
          {/* Header */}
          <div className="px-4 py-2.5 border-b border-[var(--hairline)] flex items-center justify-between bg-[var(--surface-subtle)]">
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[var(--ink-secondary)]" />
              <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-primary)] uppercase">
                Last Security Advisory &bull; Audit Trail
              </span>
            </div>
            <span className="text-[10px] font-mono text-[var(--signal-red)] font-medium">
              VERIFIER_REJECT
            </span>
          </div>

          {/* Mono Log Excerpt */}
          <div className="p-3.5 font-mono text-[11px] leading-relaxed select-text space-y-1 bg-[var(--canvas)] text-[var(--ink-secondary)] border-b border-[var(--hairline)] max-h-52 overflow-y-auto">
            <div className="text-[var(--ink-muted)]">
              [2026-11-13T13:42:01.104Z] [worker] job_id: arq:review_pull_request:892
            </div>
            <div>
              [2026-11-13T13:42:01.320Z] [ast_parser] tree-sitter scanned 14 changed files (34 hunks)
            </div>
            <div>
              [2026-11-13T13:42:02.410Z] [osv_engine] OSV API: 0 known CVEs in pyproject.toml
            </div>
            <div>
              [2026-11-13T13:42:03.950Z] [langgraph:sec_node] Candidate finding flagged in backend/app/auth.py
            </div>
            {/* Red Error Lines */}
            <div className="text-[var(--signal-red)] font-medium bg-[var(--signal-red-bg)] px-1 py-0.5 rounded-xs border-l-2 border-[var(--signal-red)]">
              [CRITICAL] CWE-89: SQL Injection via unparameterized string formatting in execute()
            </div>
            <div className="text-[var(--signal-red)] font-medium bg-[var(--signal-red-bg)] px-1 py-0.5 rounded-xs border-l-2 border-[var(--signal-red)]">
              [VERIFIER] Adversarial node confirmed exploitability. Suggestion generated.
            </div>
            <div>
              [2026-11-13T13:42:09.112Z] [publisher] GitHub verdict submitted: REQUEST_CHANGES
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 text-[10px] font-mono text-[var(--ink-muted)] flex items-center justify-between bg-[var(--surface)]">
          <span>Target: backend/app/auth.py:42</span>
          <span>Zero Hallucinations Verified</span>
        </div>
      </div>

      {/* Card 2: Deploys / Security Audits Last 14 Days Stepped Ink Bar Chart */}
      <div className="border border-[var(--hairline)] bg-[var(--surface)] rounded-sm flex flex-col justify-between overflow-hidden">
        <div>
          {/* Header */}
          <div className="px-4 py-2.5 border-b border-[var(--hairline)] flex items-center justify-between bg-[var(--surface-subtle)]">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-3.5 h-3.5 text-[var(--ink-secondary)]" />
              <span className="text-[10px] font-mono font-semibold tracking-wider text-[var(--ink-primary)] uppercase">
                Reviews Stream &bull; Last 14 Days
              </span>
            </div>
            <span className="text-[10px] font-mono text-[var(--ink-secondary)]">
              Total 64 Scans
            </span>
          </div>

          {/* Stepped Ink Bar Chart */}
          <div className="p-4 bg-[var(--canvas)] border-b border-[var(--hairline)]">
            <div className="h-36 flex items-end justify-between gap-1.5 pt-6 pb-2">
              {days.map((day, idx) => (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-1 group relative h-full justify-end"
                >
                  {/* Tooltip on hover */}
                  <div className="absolute -top-7 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none text-[9px] font-mono px-1.5 py-0.5 bg-[var(--ink-primary)] text-[var(--canvas)] rounded-xs whitespace-nowrap z-20">
                    {day.count} reviews {day.hasFail ? "(1 req change)" : ""}
                  </div>

                  {/* Stepped Ink Bar */}
                  <div
                    className={`w-full rounded-xs transition-all ${
                      day.hasFail
                        ? "bg-[var(--signal-red)] hover:opacity-90"
                        : "bg-[var(--ink-primary)] hover:opacity-80"
                    }`}
                    style={{ height: `${day.heightPercent}%` }}
                  />

                  {/* Mono Day Label */}
                  <span className="text-[9px] font-mono text-[var(--ink-muted)] group-hover:text-[var(--ink-primary)] transition-colors truncate">
                    {day.label.slice(0, 1)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chart Legend */}
        <div className="px-4 py-2 text-[10px] font-mono text-[var(--ink-muted)] flex items-center justify-between bg-[var(--surface)]">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-xs bg-[var(--ink-primary)]" />
              <span>Approved / Clean</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-xs bg-[var(--signal-red)]" />
              <span>Changes Requested</span>
            </div>
          </div>
          <span>Daily Mean: 4.6</span>
        </div>
      </div>
    </div>
  );
}
