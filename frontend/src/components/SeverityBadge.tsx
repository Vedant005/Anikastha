import { SeverityLevel } from "@/lib/types";

export function SeverityBadge({ severity }: { severity: SeverityLevel }) {
  switch (severity) {
    case "CRITICAL":
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-bold bg-[var(--signal-red-bg)] text-[var(--signal-red)] border border-[var(--signal-red-border)]">
          CRITICAL
        </span>
      );
    case "HIGH":
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-bold bg-[var(--canvas)] text-[var(--ink-primary)] border border-[var(--ink-primary)]">
          HIGH
        </span>
      );
    case "MEDIUM":
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-medium bg-[var(--canvas)] text-[var(--ink-secondary)] border border-[var(--hairline-strong)]">
          MEDIUM
        </span>
      );
    case "LOW":
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-normal bg-[var(--canvas)] text-[var(--ink-muted)] border border-[var(--hairline)]">
          LOW
        </span>
      );
    case "INFO":
    default:
      return (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded-xs text-[10px] font-mono font-normal bg-[var(--surface-subtle)] text-[var(--ink-muted)] border border-[var(--hairline)]">
          INFO
        </span>
      );
  }
}
