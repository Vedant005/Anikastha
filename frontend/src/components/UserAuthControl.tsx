"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/useAuthStore";
import { useReviewStore } from "@/store/useReviewStore";
import { getGitHubLoginUrl } from "@/lib/api";
import {
  LogOut,
  User as UserIcon,
  ChevronDown,
  Shield,
  AlertCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";

export function GitHubIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
      />
    </svg>
  );
}

interface UserAuthControlProps {
  variant?: "header" | "hero" | "cta";
}

export function UserAuthControl({ variant = "header" }: UserAuthControlProps) {
  const {
    user,
    token,
    authConfig,
    fetchAuthConfig,
    logout,
    devLogin,
    checkSession,
  } = useAuthStore();
  const { loadInitialData } = useReviewStore();

  const [isOpen, setIsOpen] = useState(false);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAuthConfig();
    checkSession();
  }, [fetchAuthConfig, checkSession]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleGitHubLogin = async () => {
    if (authConfig?.oauth_configured) {
      try {
        setIsLoggingIn(true);
        const url = await getGitHubLoginUrl();
        window.location.href = url;
      } catch (err: any) {
        alert(err.message || "Failed to initiate GitHub login");
        setIsLoggingIn(false);
      }
    } else {
      // Open modal showing test identities & setup guidance
      setIsOpen(true);
    }
  };

  const handleDevLogin = async (
    username: string,
    installationIds: number[],
  ) => {
    try {
      setIsLoggingIn(true);
      await devLogin(username, installationIds);
      await loadInitialData({ force: true });
      setIsOpen(false);
    } catch (err: any) {
      alert(err.message || "Dev login failed");
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    logout();
    useReviewStore.setState({
      repositories: [],
      reviews: [],
      selectedRepoId: null,
      lastSyncedAt: null,
    });
    setIsOpen(false);
    await loadInitialData({ force: true });
  };

  // ─────────────────────────────────────────────────────────────
  // 1. AUTHENTICATED STATE
  // ─────────────────────────────────────────────────────────────
  if (token && user) {
    if (variant === "hero" || variant === "cta") {
      return (
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer shadow-sm"
        >
          <UserIcon className="w-3.5 h-3.5" />
          <span>OPEN CONSOLE (@{user.username})</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      );
    }

    return (
      <div className="relative font-mono" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-2 px-2.5 py-1.5 text-xs border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors cursor-pointer"
          title={`Signed in as @${user.username}`}
        >
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.username}
              className="w-4 h-4 rounded-full border border-[var(--hairline)] object-cover"
            />
          ) : (
            <UserIcon className="w-3.5 h-3.5" />
          )}
          <span className="font-medium hidden sm:inline truncate max-w-[120px]">
            {user.username}
          </span>
          <ChevronDown className="w-3 h-3 text-[var(--ink-muted)]" />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-1.5 w-64 py-1.5 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm shadow-lg z-50 text-xs animate-in fade-in-50 zoom-in-95 duration-100">
            <div className="px-3 py-2 border-b border-[var(--hairline)]">
              <p className="font-semibold text-[var(--ink-primary)] truncate">
                {user.name || user.username}
              </p>
              <p className="text-[10.5px] text-[var(--ink-secondary)] truncate">
                @{user.username}
              </p>
              <div className="mt-1 flex items-center gap-1.5 text-[10px] text-[var(--ink-muted)]">
                <Shield className="w-3 h-3" />
                <span>
                  {user.installation_ids?.length || 0} active installation(s)
                </span>
              </div>
            </div>

            {/* In dev mode, show identity switcher */}
            {authConfig?.is_dev_mode && (
              <div className="px-3 py-2 border-b border-[var(--hairline)] bg-[var(--canvas)] text-[10.5px]">
                <span className="text-[var(--ink-muted)] block mb-1">
                  Switch Test Identity:
                </span>
                <div className="flex gap-1.5 flex-wrap">
                  <button
                    type="button"
                    onClick={() => handleDevLogin("developer-personal", [12345])}
                    className="px-1.5 py-0.5 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)]"
                  >
                    Personal (#12345)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDevLogin("alice-security", [11111])}
                    className="px-1.5 py-0.5 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)]"
                  >
                    Alice (#11111)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDevLogin("bob-enterprise", [22222])}
                    className="px-1.5 py-0.5 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)]"
                  >
                    Bob (#22222)
                  </button>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-[var(--signal-red)] hover:bg-[var(--signal-red-bg)] flex items-center gap-2 transition-colors cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // ─────────────────────────────────────────────────────────────
  // 2. UNAUTHENTICATED STATE
  // ─────────────────────────────────────────────────────────────
  const isHeroOrCta = variant === "hero" || variant === "cta";

  return (
    <>
      <div className="relative font-mono flex items-center" ref={dropdownRef}>
        <button
          type="button"
          onClick={handleGitHubLogin}
          disabled={isLoggingIn}
          className={
            isHeroOrCta
              ? "inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-medium rounded-sm bg-[var(--ink-primary)] text-[var(--canvas)] hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer shadow-sm"
              : "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors cursor-pointer"
          }
          title="Sign in with GitHub"
        >
          <GitHubIcon className={isHeroOrCta ? "w-4 h-4 fill-current" : "w-3.5 h-3.5 fill-current"} />
          <span>SIGN IN WITH GITHUB</span>
          {isHeroOrCta && <ArrowRight className="w-3.5 h-3.5" />}
          {!isHeroOrCta && !authConfig?.oauth_configured && (
            <ChevronDown className="w-3 h-3 text-[var(--ink-muted)]" />
          )}
        </button>
      </div>

      {/* Dev Mode Modal Dialog with full-screen backdrop */}
      {isOpen && !authConfig?.oauth_configured && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-[2px] p-4 font-mono">
          <div className="w-full max-w-sm p-5 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm shadow-xl text-xs space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-start justify-between gap-3 border-b border-[var(--hairline)] pb-3">
              <div className="flex items-center gap-2">
                <GitHubIcon className="w-4 h-4" />
                <span className="font-semibold text-sm text-[var(--ink-primary)]">
                  GitHub Sign In
                </span>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-[var(--ink-muted)] hover:text-[var(--ink-primary)] text-sm px-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1.5 text-[var(--ink-secondary)]">
              <div className="flex items-center gap-1.5 text-[var(--ink-primary)] font-medium">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Development Auth Mode</span>
              </div>
              <p className="text-[11px] leading-relaxed text-[var(--ink-muted)]">
                Live GitHub OAuth requires <code className="bg-[var(--canvas)] px-1 py-0.5 rounded-xs border border-[var(--hairline)]">GITHUB_CLIENT_ID</code> and <code className="bg-[var(--canvas)] px-1 py-0.5 rounded-xs border border-[var(--hairline)]">GITHUB_CLIENT_SECRET</code> in <code className="bg-[var(--canvas)] px-1 py-0.5 rounded-xs border border-[var(--hairline)]">.env</code>.
              </p>
            </div>

            <div className="pt-2 border-t border-[var(--hairline)] space-y-2">
              <span className="text-[10px] font-semibold text-[var(--ink-muted)] uppercase tracking-wider block">
                Select 1-Click Test Identity:
              </span>
              <div className="space-y-1.5">
                <button
                  type="button"
                  onClick={() => handleDevLogin("developer-personal", [12345])}
                  disabled={isLoggingIn}
                  className="w-full text-left px-3 py-2 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)] bg-[var(--canvas)] transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div>
                    <span className="font-medium text-[var(--ink-primary)] block">Personal Org User</span>
                    <span className="text-[10px] text-[var(--ink-muted)]">@developer-personal</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-[var(--surface)] border border-[var(--hairline)] rounded-xs text-[var(--ink-secondary)]">
                    #12345
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDevLogin("alice-security", [11111])}
                  disabled={isLoggingIn}
                  className="w-full text-left px-3 py-2 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)] bg-[var(--canvas)] transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div>
                    <span className="font-medium text-[var(--ink-primary)] block">Alice (Security Lead)</span>
                    <span className="text-[10px] text-[var(--ink-muted)]">@alice-security</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-[var(--surface)] border border-[var(--hairline)] rounded-xs text-[var(--ink-secondary)]">
                    #11111
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => handleDevLogin("bob-enterprise", [22222])}
                  disabled={isLoggingIn}
                  className="w-full text-left px-3 py-2 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)] bg-[var(--canvas)] transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div>
                    <span className="font-medium text-[var(--ink-primary)] block">Bob (Enterprise Dev)</span>
                    <span className="text-[10px] text-[var(--ink-muted)]">@bob-enterprise</span>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 bg-[var(--surface)] border border-[var(--hairline)] rounded-xs text-[var(--ink-secondary)]">
                    #22222
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
