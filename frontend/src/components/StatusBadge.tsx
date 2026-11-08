import { ReviewStatus, ReviewVerdict } from "@/lib/types";
import { CheckCircle2, Clock, AlertTriangle, XCircle, MessageSquare } from "lucide-react";

export function StatusBadge({ status }: { status: ReviewStatus }) {
  switch (status) {
    case "PENDING":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-amber-950/60 text-amber-300 border border-amber-800/60">
          <Clock className="h-3.5 w-3.5 animate-pulse" />
          Pending
        </span>
      );
    case "PROCESSING":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-cyan-950/60 text-cyan-300 border border-cyan-800/60">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping" />
          Reviewing
        </span>
      );
    case "COMPLETED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/60 text-emerald-300 border border-emerald-800/60">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Completed
        </span>
      );
    case "FAILED":
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-rose-950/60 text-rose-300 border border-rose-800/60">
          <XCircle className="h-3.5 w-3.5" />
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
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Approved
        </span>
      );
    case "REQUEST_CHANGES":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-700">
          <AlertTriangle className="h-3.5 w-3.5" />
          Changes Requested
        </span>
      );
    case "COMMENT":
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-blue-950/80 text-blue-300 border border-blue-700">
          <MessageSquare className="h-3.5 w-3.5" />
          Commented
        </span>
      );
  }
}
