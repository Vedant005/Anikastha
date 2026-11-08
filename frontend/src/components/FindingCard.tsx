import { Finding } from "@/lib/types";
import { SeverityBadge } from "./SeverityBadge";
import { ShieldCheck, FileCode, CheckCircle, AlertOctagon } from "lucide-react";

export function FindingCard({ finding }: { finding: Finding }) {
  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-all shadow-md">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <SeverityBadge severity={finding.severity} />
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
            {finding.category}
          </span>
          {finding.cve_id && (
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-900">
              {finding.cve_id}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {finding.is_verified ? (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-800/40">
              <ShieldCheck className="h-3.5 w-3.5" />
              Verified
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-400 bg-amber-950/50 px-2 py-0.5 rounded border border-amber-800/40">
              <AlertOctagon className="h-3.5 w-3.5" />
              Unverified
            </span>
          )}

          {finding.published_inline ? (
            <span className="text-xs text-cyan-400 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/30">
              Commented on Diff
            </span>
          ) : (
            <span className="text-xs text-slate-400 bg-slate-800/40 px-2 py-0.5 rounded border border-slate-700/30">
              Summary Note
            </span>
          )}
        </div>
      </div>

      <h4 className="text-base font-semibold text-slate-100 mb-2">{finding.title}</h4>

      <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono mb-3">
        <FileCode className="h-3.5 w-3.5 text-slate-500" />
        <span>{finding.file_path}</span>
        {finding.line_start && (
          <span className="text-slate-500">
            :L{finding.line_start}
            {finding.line_end && finding.line_end !== finding.line_start ? `-L${finding.line_end}` : ""}
          </span>
        )}
      </div>

      <p className="text-sm text-slate-300 leading-relaxed mb-4">{finding.description}</p>

      {finding.code_snippet && (
        <div className="mb-4">
          <div className="text-xs font-medium text-slate-400 mb-1.5">Context Code:</div>
          <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto">
            <code>{finding.code_snippet}</code>
          </pre>
        </div>
      )}

      {finding.suggestion_markdown && (
        <div className="mb-4">
          <div className="text-xs font-medium text-emerald-400 mb-1.5 flex items-center gap-1">
            <CheckCircle className="h-3.5 w-3.5" />
            Remediation Suggestion:
          </div>
          <pre className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 text-xs font-mono text-emerald-300 overflow-x-auto whitespace-pre-wrap">
            <code>{finding.suggestion_markdown}</code>
          </pre>
        </div>
      )}

      {finding.verification_reason && (
        <div className="text-xs text-slate-400 border-t border-slate-800/60 pt-3 flex items-center gap-1.5">
          <span className="font-semibold text-slate-300">Verification Note:</span>
          <span>{finding.verification_reason}</span>
        </div>
      )}
    </div>
  );
}
