"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";
import { UserAuthControl } from "./UserAuthControl";
import {
  Shield,
  Terminal,
  Cpu,
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Code2,
  FileSearch,
  Lock,
  Zap,
} from "lucide-react";

export function LandingPage({ onOpenConsole }: { onOpenConsole?: () => void }) {
  const [activeTab, setActiveTab] = useState<"code" | "cve" | "verifier">(
    "code",
  );
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(100);

  const triggerSimulatedScan = () => {
    setIsScanning(true);
    setScanProgress(20);
    setTimeout(() => setScanProgress(50), 400);
    setTimeout(() => setScanProgress(80), 800);
    setTimeout(() => {
      setScanProgress(100);
      setIsScanning(false);
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)] text-[var(--ink-primary)] flex flex-col font-sans selection:bg-[var(--ink-primary)] selection:text-[var(--canvas)]">
      {/* 1. TOP SPEC NAVIGATION BAR */}
      <header className="sticky top-0 z-30 bg-[var(--surface)] border-b border-[var(--hairline)] px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-sm border border-[var(--hairline)] bg-[var(--ink-primary)] text-[var(--canvas)] flex items-center justify-center font-mono font-bold text-xs tracking-tighter">
            PS
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm tracking-tight text-[var(--ink-primary)]">
              PR-Sentinel
            </span>
            <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-muted)] rounded-xs">
              SPEC-2026.1
            </span>
          </div>
        </div>

        {/* Center Spec Links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-mono text-[var(--ink-secondary)]">
          <a
            href="#specifications"
            className="hover:text-[var(--ink-primary)] transition-colors"
          >
            Specifications
          </a>
          <a
            href="#live-demo"
            className="hover:text-[var(--ink-primary)] transition-colors"
          >
            Live Terminal
          </a>
          <a
            href="#architecture"
            className="hover:text-[var(--ink-primary)] transition-colors"
          >
            Architecture
          </a>
          <a
            href="#comparison"
            className="hover:text-[var(--ink-primary)] transition-colors"
          >
            Comparison
          </a>
        </nav>

        {/* Right actions: Theme, Auth, Console Button */}
        <div className="flex items-center gap-2.5">
          <ThemeToggle />
          <UserAuthControl variant="header" />

          {onOpenConsole ? (
            <button
              type="button"
              onClick={onOpenConsole}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all"
            >
              <span>CONSOLE</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all"
            >
              <span>CONSOLE</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          )}
        </div>
      </header>

      {/* 2. HERO SECTION */}
      <section className="px-4 sm:px-8 py-12 lg:py-20 max-w-5xl mx-auto w-full space-y-6 text-center lg:text-left">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-xs border border-[var(--hairline)] bg-[var(--surface)] text-[10.5px] font-mono text-[var(--ink-secondary)]">
          <span className="w-2 h-2 rounded-full bg-[var(--ink-primary)]"></span>
          <span>AUTONOMOUS MULTI-AGENT PULL REQUEST SECURITY AUDITOR</span>
        </div>

        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-[var(--ink-primary)] leading-[1.08]">
          Zero-hallucination security reviews & code intelligence.
        </h1>

        <p className="text-base sm:text-lg text-[var(--ink-secondary)] max-w-3xl leading-relaxed">
          Anikastha intercepts pull requests in &lt;500ms, parses AST syntax
          trees with Tree-sitter, audits CVEs against Google OSV databases, and
          enforces adversarial LangGraph verification before publishing
          actionable inline fix suggestions.
        </p>

        {/* Hero Actions: Prominent Sign In + Console Demo */}
        <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-3">
          <UserAuthControl variant="hero" />
          {onOpenConsole && (
            <button
              type="button"
              onClick={onOpenConsole}
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-mono font-medium border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-all cursor-pointer"
            >
              <span>EXPLORE DEMO CONSOLE</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Spec stat bar */}
        <div className="pt-2 flex flex-wrap items-center justify-center lg:justify-start gap-4 sm:gap-6 text-xs font-mono text-[var(--ink-muted)]">
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-[var(--ink-primary)]" />
            <span>&lt;500ms Webhook HMAC</span>
          </div>
          <span className="hidden sm:inline">&bull;</span>
          <div className="flex items-center gap-1.5">
            <Code2 className="w-3.5 h-3.5 text-[var(--ink-primary)]" />
            <span>Tree-Sitter AST Sinks</span>
          </div>
          <span className="hidden sm:inline">&bull;</span>
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-[var(--ink-primary)]" />
            <span>Multi-Tenant GitHub OAuth</span>
          </div>
          <span className="hidden sm:inline">&bull;</span>
          <div className="flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-[var(--ink-primary)]" />
            <span>Zero Hallucinated Lines</span>
          </div>
        </div>
      </section>

      {/* 3. INTERACTIVE LIVE TERMINAL SIMULATION */}
      <section
        id="live-demo"
        className="px-4 sm:px-8 py-6 max-w-5xl mx-auto w-full space-y-3"
      >
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-[var(--ink-secondary)]">
            <Terminal className="w-4 h-4 text-[var(--ink-primary)]" />
            <span className="font-semibold uppercase text-[var(--ink-primary)]">
              Interactive Review Console
            </span>
            <span className="text-[var(--ink-muted)]">
              // PR #42 &bull; secure-service
            </span>
          </div>

          <button
            type="button"
            onClick={triggerSimulatedScan}
            disabled={isScanning}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
          >
            <span
              className={`w-2 h-2 rounded-full ${isScanning ? "bg-[var(--signal-red)] animate-ping" : "bg-[var(--ink-primary)]"}`}
            />
            <span>
              {isScanning ? `ANALYZING (${scanProgress}%)` : "RE-SCAN PR"}
            </span>
          </button>
        </div>

        {/* Terminal Container */}
        <div className="border border-[var(--hairline)] rounded-sm bg-[var(--surface)] overflow-hidden font-mono text-xs">
          {/* Terminal Tabs */}
          <div className="flex items-center justify-between border-b border-[var(--hairline)] bg-[var(--canvas)] px-3 py-1.5 overflow-x-auto">
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setActiveTab("code")}
                className={`px-2.5 py-1 rounded-xs transition-colors ${
                  activeTab === "code"
                    ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
                    : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
                }`}
              >
                1. AST Code Diff (CWE-502)
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("cve")}
                className={`px-2.5 py-1 rounded-xs transition-colors ${
                  activeTab === "cve"
                    ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
                    : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
                }`}
              >
                2. OSV CVE Audit
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("verifier")}
                className={`px-2.5 py-1 rounded-xs transition-colors ${
                  activeTab === "verifier"
                    ? "bg-[var(--surface)] text-[var(--ink-primary)] font-medium border border-[var(--hairline)]"
                    : "text-[var(--ink-secondary)] hover:text-[var(--ink-primary)]"
                }`}
              >
                3. Adversarial Verifier & Verdict
              </button>
            </div>

            <span className="hidden sm:inline text-[10px] text-[var(--ink-muted)]">
              PIPELINE: LANGGRAPH-V2
            </span>
          </div>

          {/* Terminal Content Body */}
          <div className="p-4 sm:p-6 overflow-x-auto text-[11.5px] leading-relaxed">
            {activeTab === "code" && (
              <div className="space-y-3">
                <div className="text-[var(--ink-muted)] flex items-center justify-between">
                  <span>
                    diff --git a/app/services/session.py
                    b/app/services/session.py
                  </span>
                  <span className="text-[var(--signal-red)] font-semibold">
                    CRITICAL FINDING
                  </span>
                </div>
                <div className="p-3 bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs space-y-1">
                  <div className="text-[var(--ink-muted)]">
                    @@ -14,6 +14,8 @@ def parse_user_payload(raw_token: bytes):
                  </div>
                  <div className="text-[var(--ink-secondary)]">
                    {" "}
                    header, payload = decode_envelope(raw_token)
                  </div>
                  <div className="text-[var(--signal-red)] bg-[var(--signal-red-bg)] px-1 rounded-xs">
                    + # INSECURE SINK: Deserialization without schema validation
                  </div>
                  <div className="text-[var(--signal-red)] bg-[var(--signal-red-bg)] px-1 rounded-xs">
                    + session_obj = pickle.loads(payload)
                  </div>
                  <div className="text-[var(--ink-secondary)]">
                    {" "}
                    return session_obj.validate_permissions()
                  </div>
                </div>
                <div className="p-2 border border-[var(--hairline)] bg-[var(--surface)] rounded-xs text-[var(--ink-secondary)] flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-[var(--signal-red)] flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-[var(--ink-primary)]">
                      CWE-502: Deserialization of Untrusted Data
                    </span>
                    <p className="text-[11px] text-[var(--ink-muted)]">
                      Tree-sitter detected sink `pickle.loads` called on
                      parameter `payload` without prior cryptographic signature
                      validation or schema bounds.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "cve" && (
              <div className="space-y-3">
                <div className="text-[var(--ink-muted)] flex items-center justify-between">
                  <span>
                    dependency_parser // requirements.txt & pyproject.toml
                  </span>
                  <span className="text-[var(--ink-primary)] font-semibold">
                    1 VULNERABILITY DETECTED
                  </span>
                </div>
                <div className="p-3 bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[var(--signal-red)] font-semibold">
                      PyYAML @ 5.3.1 &rarr; CVE-2020-14343 (CVSS 9.8)
                    </span>
                    <span className="px-1.5 py-0.5 text-[10px] bg-[var(--signal-red-bg)] text-[var(--signal-red)] border border-[var(--signal-red-border)] rounded-xs">
                      CRITICAL
                    </span>
                  </div>
                  <p className="text-[var(--ink-secondary)]">
                    Arbitrary code execution vulnerability in PyYAML loader.
                    Fixed in version 5.4.
                  </p>
                  <div className="pt-1 text-[var(--ink-muted)] text-[11px]">
                    License check:{" "}
                    <span className="text-[var(--ink-primary)] font-semibold">
                      MIT License
                    </span>{" "}
                    &bull; Compliance status:{" "}
                    <span className="text-[var(--ink-primary)] font-medium">
                      ALLOWED
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "verifier" && (
              <div className="space-y-3">
                <div className="text-[var(--ink-muted)] flex items-center justify-between">
                  <span>
                    adversarial_verifier_gate // LangGraph Node 4 of 5
                  </span>
                  <span className="text-[var(--ink-primary)] font-semibold">
                    &check; PASSED VERIFICATION
                  </span>
                </div>
                <div className="p-3 bg-[var(--canvas)] border border-[var(--hairline)] rounded-xs space-y-2">
                  <div className="text-[var(--ink-primary)] font-semibold">
                    Automated GitHub Review Verdict:{" "}
                    <span className="text-[var(--signal-red)]">
                      REQUEST_CHANGES
                    </span>
                  </div>
                  <p className="text-[var(--ink-secondary)]">
                    Hunk coordinates verified: lines 15-16 strictly within PR
                    diff hunk. Verified not a false-positive pattern.
                  </p>
                  <div className="p-2.5 border border-[var(--hairline)] bg-[var(--canvas)] rounded-xs space-y-1">
                    <div className="text-[10px] text-[var(--ink-muted)] uppercase tracking-wider font-semibold">
                      Proposed Inline Code Suggestion:
                    </div>
                    <pre className="text-[11px] text-[var(--ink-primary)] overflow-x-auto">
                      {`\`\`\`suggestion
    # SAFE: Use JSON or schema-bounded serializer with strict typing
    session_obj = UserSession.model_validate_json(payload)
\`\`\``}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 4. SPECIFICATIONS GRID */}
      <section
        id="specifications"
        className="px-4 sm:px-8 py-16 max-w-5xl mx-auto w-full space-y-8"
      >
        <div className="space-y-2">
          <span className="text-xs font-mono text-[var(--ink-muted)] uppercase tracking-widest font-semibold">
            ENGINEERING CONTRACT
          </span>
          <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-[var(--ink-primary)]">
            Architectural Specifications
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Spec 1 */}
          <div className="p-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm space-y-3">
            <span className="text-xs font-mono text-[var(--ink-muted)]">
              SPEC-01 // ZERO-HALLUCINATION GATE
            </span>
            <h3 className="text-base font-semibold text-[var(--ink-primary)]">
              Strict Diff Hunk Pinning
            </h3>
            <p className="text-xs text-[var(--ink-secondary)] leading-relaxed">
              Traditional AI reviewers generate unprocessable comments on line
              coordinates outside the git diff hunk. PR-Sentinel validates every
              finding against the diff AST before posting, avoiding GitHub API
              422 errors and developer frustration.
            </p>
          </div>

          {/* Spec 2 */}
          <div className="p-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm space-y-3">
            <span className="text-xs font-mono text-[var(--ink-muted)]">
              SPEC-02 // AST STATIC ANALYSIS
            </span>
            <h3 className="text-base font-semibold text-[var(--ink-primary)]">
              Tree-Sitter Syntax Inspection
            </h3>
            <p className="text-xs text-[var(--ink-secondary)] leading-relaxed">
              Static AST inspection parses Python and TypeScript syntax trees
              directly. Detects dangerous sink invocations (eval, pickle, SQL
              string concatenation, shell commands) without executing untrusted
              PR code in the host.
            </p>
          </div>

          {/* Spec 3 */}
          <div className="p-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm space-y-3">
            <span className="text-xs font-mono text-[var(--ink-muted)]">
              SPEC-03 // ASYNC WORKER INGESTION
            </span>
            <h3 className="text-base font-semibold text-[var(--ink-primary)]">
              Sub-500ms Webhook Latency
            </h3>
            <p className="text-xs text-[var(--ink-secondary)] leading-relaxed">
              Webhook signatures are validated using constant-time HMAC-SHA256
              comparison and immediately enqueued to Redis/ARQ. Fast route
              handlers acknowledge GitHub immediately, preventing webhook
              delivery timeouts.
            </p>
          </div>

          {/* Spec 4 */}
          <div className="p-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm space-y-3">
            <span className="text-xs font-mono text-[var(--ink-muted)]">
              SPEC-04 // MULTI-TENANCY ISOLATION
            </span>
            <h3 className="text-base font-semibold text-[var(--ink-primary)]">
              GitHub OAuth Tenant Scoping
            </h3>
            <p className="text-xs text-[var(--ink-secondary)] leading-relaxed">
              Every repository, policy, and review run is strictly partitioned
              by the authorized GitHub installation IDs of the signed-in user.
              Developers and organizations never view or cross-contaminate audit
              records from other tenants.
            </p>
          </div>
        </div>
      </section>

      {/* 5. COMPARISON TABLE */}
      <section
        id="comparison"
        className="px-4 sm:px-8 py-12 max-w-5xl mx-auto w-full space-y-6"
      >
        <div className="space-y-2">
          <span className="text-xs font-mono text-[var(--ink-muted)] uppercase tracking-widest font-semibold">
            BENCHMARK ANALYSIS
          </span>
          <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-[var(--ink-primary)]">
            How PR-Sentinel Compares
          </h2>
        </div>

        <div className="border border-[var(--hairline)] rounded-sm bg-[var(--surface)] overflow-x-auto font-mono text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-muted)]">
                <th className="p-3.5 font-medium">Capability</th>
                <th className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  PR-Sentinel
                </th>
                <th className="p-3.5 font-medium">Generic LLM PR Bots</th>
                <th className="p-3.5 font-medium">Legacy Static SAST</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--hairline)]">
              <tr>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  Diff Hunk Line Verification
                </td>
                <td className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  &check; Pinned & Verified
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; Prone to 422 drift
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; Whole file only
                </td>
              </tr>
              <tr>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  Adversarial False-Positive Gate
                </td>
                <td className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  &check; LangGraph Gate
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; High noise ratio
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; Hardcoded rules
                </td>
              </tr>
              <tr>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  Tree-Sitter AST Structural Analysis
                </td>
                <td className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  &check; Native AST Trees
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; Raw string prompt
                </td>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  &check; Static trees
                </td>
              </tr>
              <tr>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  Automated Code Fix Suggestions
                </td>
                <td className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  &check; GitHub ````suggestion
                </td>
                <td className="p-3.5 text-[var(--ink-secondary)]">
                  Vague advice
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">
                  &cross; Warning only
                </td>
              </tr>
              <tr>
                <td className="p-3.5 text-[var(--ink-primary)]">
                  Multi-Tenant Installation Isolation
                </td>
                <td className="p-3.5 font-semibold text-[var(--ink-primary)]">
                  &check; GitHub OAuth Scoped
                </td>
                <td className="p-3.5 text-[var(--ink-muted)]">Single tenant</td>
                <td className="p-3.5 text-[var(--ink-secondary)]">
                  Proprietary accounts
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* 6. CALL TO ACTION SPEC CARD */}
      <section className="px-4 sm:px-8 py-16 max-w-5xl mx-auto w-full">
        <div className="p-8 sm:p-12 border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-center space-y-6">
          <div className="max-w-xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight text-[var(--ink-primary)]">
              Ready to automate PR security reviews?
            </h2>
            <p className="text-xs sm:text-sm text-[var(--ink-secondary)]">
              Sign in with your GitHub account to connect repositories and run
              autonomous security audits on every pull request.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <UserAuthControl variant="cta" />
            {onOpenConsole ? (
              <button
                type="button"
                onClick={onOpenConsole}
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-medium rounded-sm border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-all cursor-pointer"
              >
                <span>OPEN DEVELOPER CONSOLE</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <Link
                href="/"
                className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-medium rounded-sm border border-[var(--hairline)] bg-[var(--canvas)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-all"
              >
                <span>OPEN DEVELOPER CONSOLE</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}

            <Link
              href="/repositories"
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono border border-[var(--hairline)] rounded-sm bg-[var(--canvas)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
            >
              <span>CONNECT REPOSITORIES</span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
