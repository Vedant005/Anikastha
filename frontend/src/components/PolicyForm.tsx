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
    initialPolicy?.prohibited_licenses?.join(", ") ||
      "GPL-3.0, AGPL-3.0, SSPL-1.0"
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
    <form
      onSubmit={handleSave}
      className="space-y-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm p-5 sm:p-6"
    >
      <div className="border-b border-[var(--hairline)] pb-4">
        <h3 className="text-sm font-semibold tracking-tight text-[var(--ink-primary)]">
          Repository Review &amp; Verdict Policy
        </h3>
        <p className="text-xs text-[var(--ink-secondary)] mt-1 font-mono">
          Configure how PR-Sentinel evaluates security findings and gates GitHub PR merges.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xs bg-[var(--signal-red-bg)] border border-[var(--signal-red-border)] text-[var(--signal-red)] text-xs font-mono">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-xs bg-[var(--canvas)] border border-[var(--hairline-strong)] text-[var(--ink-primary)] text-xs font-mono">
          <Check className="w-4 h-4 flex-shrink-0" />
          <span>Security policy saved to repository ledger.</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div>
          <label className="block text-xs font-mono font-medium text-[var(--ink-secondary)] mb-2">
            Block PR on Minimum Severity
          </label>
          <select
            value={failOnSeverity}
            onChange={(e) =>
              setFailOnSeverity(e.target.value as SeverityLevel)
            }
            className="w-full bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs px-3 py-2 text-xs font-mono text-[var(--ink-primary)] focus:outline-none focus:border-[var(--ink-primary)]"
          >
            <option value="CRITICAL">Critical only</option>
            <option value="HIGH">High &amp; Critical (Recommended)</option>
            <option value="MEDIUM">Medium, High &amp; Critical</option>
            <option value="LOW">All findings (Low to Critical)</option>
          </select>
        </div>

        <div className="space-y-3 font-mono">
          <label className="block text-xs font-medium text-[var(--ink-secondary)]">
            Automation Gates
          </label>
          <div className="flex items-start gap-2.5">
            <input
              type="checkbox"
              id="autoRequest"
              checked={autoRequestChanges}
              onChange={(e) => setAutoRequestChanges(e.target.checked)}
              className="mt-0.5 rounded-xs accent-[var(--ink-primary)]"
            />
            <label
              htmlFor="autoRequest"
              className="text-xs text-[var(--ink-secondary)] cursor-pointer select-none leading-tight"
            >
              Automatically post <code className="text-[var(--ink-primary)]">REQUEST_CHANGES</code> when threshold is breached
            </label>
          </div>

          <div className="flex items-start gap-2.5">
            <input
              type="checkbox"
              id="blockLicenses"
              checked={blockLicenses}
              onChange={(e) => setBlockLicenses(e.target.checked)}
              className="mt-0.5 rounded-xs accent-[var(--ink-primary)]"
            />
            <label
              htmlFor="blockLicenses"
              className="text-xs text-[var(--ink-secondary)] cursor-pointer select-none leading-tight"
            >
              Block pull requests introducing prohibited open-source licenses
            </label>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-xs font-mono font-medium text-[var(--ink-secondary)] mb-2">
          Prohibited Licenses (comma-separated SPDX IDs)
        </label>
        <input
          type="text"
          value={prohibitedLicensesText}
          onChange={(e) => setProhibitedLicensesText(e.target.value)}
          placeholder="GPL-3.0, AGPL-3.0, SSPL-1.0"
          className="w-full bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs px-3 py-2 text-xs font-mono text-[var(--ink-primary)] focus:outline-none focus:border-[var(--ink-primary)]"
        />
      </div>

      <div className="flex justify-end pt-2 border-t border-[var(--hairline)]">
        <button
          type="submit"
          disabled={isSaving}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xs bg-[var(--ink-primary)] text-[var(--canvas)] text-xs font-mono font-medium hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          <Save className="w-3.5 h-3.5" />
          {isSaving ? "SAVING POLICY..." : "SAVE POLICY"}
        </button>
      </div>
    </form>
  );
}
