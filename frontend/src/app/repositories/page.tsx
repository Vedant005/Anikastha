"use client";

import { useEffect, useState } from "react";
import { fetchRepositories } from "@/lib/api";
import { Repository } from "@/lib/types";
import { PolicyForm } from "@/components/PolicyForm";
import { GitBranch, Shield, RefreshCw, CheckCircle2 } from "lucide-react";

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Repositories & Security Policy
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage connected GitHub repositories and configure branch protection
            & review verdict policies.
          </p>
        </div>

        <button
          onClick={loadRepos}
          className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white transition-colors"
          title="Refresh repositories"
        >
          <RefreshCw
            className={`h-4 w-4 ${isLoading ? "animate-spin text-cyan-400" : ""}`}
          />
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-300 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Repositories Sidebar */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Connected Repositories ({repositories.length})
          </h2>

          {repositories.length === 0 && !isLoading ? (
            <div className="p-6 text-center rounded-xl bg-slate-900/30 border border-slate-800 text-slate-500 text-sm">
              No repositories connected. Install the PR-Sentinel GitHub App on a
              repository to get started.
            </div>
          ) : (
            <div className="space-y-2">
              {repositories.map((repo) => (
                <button
                  key={repo.id}
                  onClick={() => setSelectedRepo(repo)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    selectedRepo?.id === repo.id
                      ? "bg-slate-900 border-cyan-500 shadow-md shadow-cyan-950/20"
                      : "bg-slate-900/40 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-100 text-sm flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-cyan-400" />
                      {repo.full_name}
                    </span>
                    {repo.is_active && (
                      <span className="flex items-center gap-1 text-[10px] font-medium text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/40">
                        <CheckCircle2 className="h-3 w-3" />
                        Active
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500 mt-2 font-mono">
                    Installation ID: {repo.installation_id}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Policy Editor Form */}
        <div className="lg:col-span-2 space-y-4">
          {selectedRepo ? (
            <div>
              <div className="mb-4">
                <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                  Configuring Policy For
                </span>
                <h3 className="text-xl font-bold text-white">
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
            <div className="p-12 text-center rounded-xl bg-slate-900/20 border border-slate-800 text-slate-500 text-sm">
              Select a repository on the left to configure its security policy.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
