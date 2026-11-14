"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchRepositories } from "@/lib/api";
import { Repository } from "@/lib/types";
import { PolicyForm } from "@/components/PolicyForm";
import { InkGlyph } from "@/components/InkGlyph";
import { ArrowLeft, GitBranch, RefreshCw, Plus, ExternalLink, Menu } from "lucide-react";
import { useSidebar } from "@/components/SidebarContext";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toggleSidebar } = useSidebar();

  const loadRepos = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchRepositories();
      setRepositories(data);
      if (data.length > 0 && !selectedRepo) {
        setSelectedRepo(data[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load repositories");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadRepos();
  }, []);

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-[1440px] w-full mx-auto">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-[var(--hairline)]">
        <div className="flex items-center gap-2 text-xs font-mono">
          <button
            type="button"
            onClick={toggleSidebar}
            className="p-1.5 rounded-sm border border-[var(--hairline)] bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] lg:hidden flex-shrink-0"
            aria-label="Open navigation menu"
          >
            <Menu className="w-4 h-4" />
          </button>
          <Link
            href="/"
            className="text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
          >
            reviews
          </Link>
          <span className="text-[var(--ink-muted)]">/</span>
          <span className="text-[var(--ink-primary)] font-medium">repositories &amp; policy</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadRepos}
            className="p-1.5 rounded-sm border border-[var(--hairline)] bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
            title="Refresh repositories"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 ${
                isLoading ? "animate-spin text-[var(--ink-primary)]" : ""
              }`}
            />
          </button>
          <a
            href="https://github.com/apps/pr-sentinel"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 transition-opacity"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>INSTALL GITHUB APP</span>
          </a>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xs bg-[var(--signal-red-bg)] border border-[var(--signal-red-border)] text-[var(--signal-red)] text-xs font-mono">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Repositories List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[var(--ink-muted)]">
              Connected Repositories ({repositories.length})
            </h2>
          </div>

          {repositories.length === 0 && !isLoading ? (
            <div className="p-6 text-center rounded-sm bg-[var(--surface)] border border-[var(--hairline)] text-[var(--ink-muted)] text-xs font-mono">
              No repositories connected yet. Install the GitHub App to enroll repositories.
            </div>
          ) : (
            <div className="space-y-1.5">
              {repositories.map((repo) => {
                const isSelected = selectedRepo?.id === repo.id;
                return (
                  <button
                    key={repo.id}
                    onClick={() => setSelectedRepo(repo)}
                    className={`w-full text-left p-3.5 rounded-sm border transition-colors ${
                      isSelected
                        ? "bg-[var(--surface)] border-[var(--ink-primary)]"
                        : "bg-[var(--surface)] border-[var(--hairline)] hover:border-[var(--hairline-strong)]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-[var(--ink-primary)] text-xs flex items-center gap-2 truncate">
                        <InkGlyph
                          type={repo.is_active ? "ready" : "canceled"}
                          size="sm"
                        />
                        <span className="truncate">{repo.full_name}</span>
                      </span>
                      {repo.is_active && (
                        <span className="text-[9px] font-mono border border-[var(--hairline)] bg-[var(--canvas)] px-1.5 py-0.2 rounded-xs text-[var(--ink-secondary)]">
                          ACTIVE
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-[var(--ink-muted)] mt-1.5 font-mono">
                      Installation ID: {repo.installation_id}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Policy Editor Form */}
        <div className="lg:col-span-2 space-y-4">
          {selectedRepo ? (
            <div>
              <div className="mb-4">
                <span className="text-[10px] font-mono text-[var(--ink-muted)] uppercase tracking-wider">
                  Target Repository
                </span>
                <h3 className="text-base font-bold text-[var(--ink-primary)]">
                  {selectedRepo.full_name}
                </h3>
              </div>

              <PolicyForm
                key={selectedRepo.id}
                repoId={selectedRepo.id}
                initialPolicy={selectedRepo.policy}
              />
            </div>
          ) : (
            <div className="p-12 text-center rounded-sm bg-[var(--surface)] border border-[var(--hairline)] text-[var(--ink-muted)] text-xs font-mono">
              Select a repository on the left to configure its security verdict policy.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
