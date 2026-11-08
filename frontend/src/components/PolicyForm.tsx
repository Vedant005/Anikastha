"use client";

import { useState } from "react";
import { Policy, SeverityLevel } from "@/lib/types";
import { updateRepositoryPolicy } from "@/lib/api";
import { Save, Check, AlertCircle } from "lucide-react";

export function PolicyForm({
  repoId,
  initialPolicy,
}: {
  repoId: string;
  initialPolicy?: Policy;
}) {
  const [failOnSeverity, setFailOnSeverity] = useState<SeverityLevel>(
    initialPolicy?.fail_on_severity || "HIGH"
  );
  const [blockLicenses, setBlockLicenses] = useState<boolean>(
    initialPolicy?.block_prohibited_licenses ?? true
  );
  const [autoRequestChanges, setAutoRequestChanges] = useState<boolean>(
    initialPolicy?.auto_request_changes ?? true
  );
  const [prohibitedLicensesText, setProhibitedLicensesText] = useState<string>(
    initialPolicy?.prohibited_licenses?.join(", ") || "GPL-3.0, AGPL-3.0, SSPL-1.0"
  );

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess(false);
    setError(null);

    const licensesList = prohibitedLicensesText
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    try {
      await updateRepositoryPolicy(repoId, {
        fail_on_severity: failOnSeverity,
        block_prohibited_licenses: blockLicenses,
        auto_request_changes: autoRequestChanges,
        prohibited_licenses: licensesList,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setError(err.message || "Failed to update policy");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6 bg-slate-900/40 border border-slate-800 rounded-xl p-6">
      <div>
        <h3 className="text-base font-semibold text-slate-100">Review Verdict Policy</h3>
        <p className="text-xs text-slate-400 mt-1">
          Configure how PR-Sentinel determines review verdicts and blocking rules on GitHub PRs.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-emerald-300 text-sm">
          <Check className="h-4 w-4" />
          <span>Policy saved successfully!</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-2">
            Block PR on Minimum Severity
          </label>
          <select
            value={failOnSeverity}
            onChange={(e) => setFailOnSeverity(e.target.value as SeverityLevel)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
          >
            <option value="CRITICAL">Critical only</option>
            <option value="HIGH">High & Critical (Recommended)</option>
            <option value="MEDIUM">Medium, High & Critical</option>
            <option value="LOW">All findings (Low to Critical)</option>
          </select>
        </div>

        <div className="space-y-3">
          <label className="block text-xs font-medium text-slate-300">Automation Settings</label>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="autoRequest"
              checked={autoRequestChanges}
              onChange={(e) => setAutoRequestChanges(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0"
            />
            <label htmlFor="autoRequest" className="text-xs text-slate-300 cursor-pointer">
              Automatically post <code>REQUEST_CHANGES</code> when policy threshold is triggered
            </label>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="blockLicenses"
              checked={blockLicenses}
              onChange={(e) => setBlockLicenses(e.target.checked)}
              className="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0"
            />
            <label htmlFor="blockLicenses" className="text-xs text-slate-300 cursor-pointer">
              Block pull requests introducing prohibited licenses
            </label>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-300 mb-2">
          Prohibited Licenses (comma-separated SPDX identifiers)
        </label>
        <input
          type="text"
          value={prohibitedLicensesText}
          onChange={(e) => setProhibitedLicensesText(e.target.value)}
          placeholder="GPL-3.0, AGPL-3.0, SSPL-1.0"
          className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
        />
      </div>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {isSaving ? "Saving..." : "Save Policy"}
        </button>
      </div>
    </form>
  );
}
