import { Finding } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";
import { ShieldCheck, FileCode, CheckCircle2, AlertOctagon, Terminal } from "lucide-react";

export function FindingCard({ finding }: { finding: Finding }) {
  const isCritical = finding.severity === "CRITICAL";

  return (
    <div
      className={`border rounded-sm p-4 sm:p-5 transition-colors ${
        isCritical
          ? "border-[var(--signal-red-border)] bg-[var(--surface)]"
          : "border-[var(--hairline)] bg-[var(--surface)] hover:border-[var(--hairline-strong)]"
      }`}
    >
      {/* Top Meta Line */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 mb-3">
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-[var(--ink-secondary)]">
            {finding.category}
          </span>
          {finding.cve_id && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-xs bg-[var(--signal-red-bg)] text-[var(--signal-red)] border border-[var(--signal-red-border)]">
              {finding.cve_id}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          {finding.is_verified ? (
            <span className="inline-flex items-center gap-1 text-[var(--ink-primary)] font-medium border border-[var(--hairline)] bg-[var(--canvas)] px-1.5 py-0.5 rounded-xs">
              <ShieldCheck className="w-3 h-3 text-[var(--ink-primary)]" />
              Adversarial Verified
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[var(--ink-muted)] border border-[var(--hairline)] bg-[var(--canvas)] px-1.5 py-0.5 rounded-xs">
              <AlertOctagon className="w-3 h-3" />
              Unverified
            </span>
          )}

          {finding.published_inline ? (
            <span className="text-[var(--ink-secondary)] border border-[var(--hairline)] bg-[var(--canvas)] px-1.5 py-0.5 rounded-xs">
              Diff Commented
            </span>
          ) : (
            <span className="text-[var(--ink-muted)] border border-[var(--hairline)] bg-[var(--canvas)] px-1.5 py-0.5 rounded-xs">
              Summary
            </span>
          )}
        </div>
      </div>

      {/* Finding Title */}
      <h4
        className={`text-sm font-semibold tracking-tight mb-1.5 ${
          isCritical ? "text-[var(--signal-red)]" : "text-[var(--ink-primary)]"
        }`}
      >
        {finding.title}
      </h4>

      {/* File Path & Coordinates */}
      <div className="flex items-center gap-1.5 text-xs text-[var(--ink-muted)] font-mono mb-3">
        <FileCode className="w-3.5 h-3.5 text-[var(--ink-secondary)]" />
        <span className="text-[var(--ink-secondary)]">{finding.file_path}</span>
        {finding.line_start && (
          <span>
            :L{finding.line_start}
            {finding.line_end && finding.line_end !== finding.line_start
              ? `-L${finding.line_end}`
              : ""}
          </span>
        )}
      </div>

      {/* Description */}
      <p className="text-xs sm:text-sm text-[var(--ink-secondary)] leading-relaxed mb-4">
        {finding.description}
      </p>

      {/* Code Snippet */}
      {finding.code_snippet && (
        <div className="mb-4">
          <div className="text-[10px] font-mono uppercase text-[var(--ink-muted)] mb-1">
            Offending Context Code
          </div>
          <pre className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline)] text-xs font-mono text-[var(--ink-primary)] overflow-x-auto leading-relaxed">
            <code>{finding.code_snippet}</code>
          </pre>
        </div>
      )}

      {/* Remediation Suggestion (GitHub Diff Suggestion style) */}
      {finding.suggestion_markdown && (
        <div className="mb-4">
          <div className="text-[10px] font-mono uppercase text-[var(--ink-primary)] font-semibold mb-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-[var(--ink-primary)]" />
            Remediation Patch
          </div>
          <pre className="p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline-strong)] text-xs font-mono text-[var(--ink-primary)] overflow-x-auto whitespace-pre-wrap leading-relaxed">
            <code>{finding.suggestion_markdown}</code>
          </pre>
        </div>
      )}

      {/* Verification Reason */}
      {finding.verification_reason && (
        <div className="text-[11px] font-mono text-[var(--ink-muted)] border-t border-[var(--hairline)] pt-2.5 flex items-center gap-1.5">
          <span className="font-semibold text-[var(--ink-secondary)]">
            Verifier Verdict:
          </span>
          <span>{finding.verification_reason}</span>
        </div>
      )}
    </div>
  );
}
