import { SeverityLevel } from "@/lib/types";

export function SeverityBadge({ severity }: { severity: SeverityLevel }) {
  switch (severity) {
    case "CRITICAL":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
          CRITICAL
        </span>
      );
    case "HIGH":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-orange-500/10 text-orange-400 border border-orange-500/30">
          HIGH
        </span>
      );
    case "MEDIUM":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
          MEDIUM
        </span>
      );
    case "LOW":
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30">
          LOW
        </span>
      );
    case "INFO":
    default:
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-500/30">
          INFO
        </span>
      );
  }
}
