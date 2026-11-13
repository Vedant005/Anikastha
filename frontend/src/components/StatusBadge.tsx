import { ReviewStatus, ReviewVerdict } from "@/lib/types";
import { InkGlyph } from "./InkGlyph";

export function StatusBadge({ status }: { status: ReviewStatus }) {
  switch (status) {
    case "PENDING":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)]">
          <InkGlyph type="pending" size="sm" />
          Pending
        </span>
      );
    case "PROCESSING":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--hairline)] bg-[var(--surface-subtle)] text-[var(--ink-primary)]">
          <InkGlyph type="processing" size="sm" />
          Processing
        </span>
      );
    case "COMPLETED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-primary)]">
          <InkGlyph type="ready" size="sm" />
          Completed
        </span>
      );
    case "FAILED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--signal-red-border)] bg-[var(--signal-red-bg)] text-[var(--signal-red)] font-medium">
          <InkGlyph type="failed" size="sm" />
          Failed
        </span>
      );
  }
}

export function VerdictBadge({ verdict }: { verdict?: ReviewVerdict }) {
  if (!verdict) return null;

  switch (verdict) {
    case "APPROVE":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--hairline-strong)] bg-[var(--canvas)] text-[var(--ink-primary)] font-medium">
          <InkGlyph type="approved" size="sm" />
          Approved
        </span>
      );
    case "REQUEST_CHANGES":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--signal-red-border)] bg-[var(--signal-red-bg)] text-[var(--signal-red)] font-semibold">
          <InkGlyph type="failed" size="sm" />
          Changes Requested
        </span>
      );
    case "COMMENT":
      return (
        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-xs text-[11px] font-mono border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-secondary)]">
          <InkGlyph type="comment" size="sm" />
          Commented
        </span>
      );
  }
}
