"use client";

import React, { useEffect, useState, useRef } from "react";
import Image from "next/image";
import { useAuthStore } from "@/store/useAuthStore";
import { useReviewStore } from "@/store/useReviewStore";
import { getGitHubLoginUrl } from "@/lib/api";
import {
  LogOut,
  User as UserIcon,
  ChevronDown,
  Shield,
  Laptop,
} from "lucide-react";

function GitHubIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
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

export function UserAuthControl() {
  const { user, token, authConfig, fetchAuthConfig, logout, devLogin, checkSession } =
    useAuthStore();
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
    try {
      setIsLoggingIn(true);
      const url = await getGitHubLoginUrl();
      window.location.href = url;
    } catch (err: any) {
      alert(err.message || "Failed to initiate GitHub login");
      setIsLoggingIn(false);
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
    setIsOpen(false);
    await loadInitialData({ force: true });
  };

  // If user is authenticated: show avatar + username + dropdown
  if (token && user) {
    return (
      <div className="relative font-mono" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-2 px-2 py-1 text-xs border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
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
          <span className="font-medium hidden md:inline truncate max-w-[100px]">
            {user.username}
          </span>
          <ChevronDown className="w-3 h-3 text-[var(--ink-muted)]" />
        </button>

        {isOpen && (
          <div className="absolute right-0 mt-1.5 w-60 py-1.5 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm shadow-xs z-50 text-xs">
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
                    onClick={() => handleDevLogin("alice", [11111])}
                    className="px-1.5 py-0.5 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)]"
                  >
                    Alice (11111)
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDevLogin("bob", [22222])}
                    className="px-1.5 py-0.5 border border-[var(--hairline)] rounded-xs hover:border-[var(--ink-primary)]"
                  >
                    Bob (22222)
                  </button>
                </div>
              </div>
            )}

            <button
              type="button"
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 text-[var(--signal-red)] hover:bg-[var(--signal-red-bg)] flex items-center gap-2 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    );
  }

  // If user is unauthenticated:
  return (
    <div className="relative font-mono flex items-center gap-1.5" ref={dropdownRef}>
      {authConfig?.oauth_configured ? (
        <button
          type="button"
          onClick={handleGitHubLogin}
          disabled={isLoggingIn}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors"
          title="Sign in with GitHub"
        >
          <GitHubIcon className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Sign in</span>
        </button>
      ) : null}

      {/* Dev Login Helper when OAuth is not configured or in dev mode */}
      {authConfig?.is_dev_mode && (
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className="inline-flex items-center gap-1.5 px-2 py-1 text-xs border border-dashed border-[var(--hairline)] rounded-sm bg-transparent text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] transition-colors"
          title="Quick Dev Login for Testing Multi-Tenancy"
        >
          <Laptop className="w-3 h-3" />
          <span className="hidden lg:inline text-[11px]">Dev Auth</span>
          <ChevronDown className="w-2.5 h-2.5 text-[var(--ink-muted)]" />
        </button>
      )}

      {isOpen && authConfig?.is_dev_mode && (
        <div className="absolute right-0 mt-1.5 top-full w-52 py-2 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm shadow-xs z-50 text-xs">
          <div className="px-3 pb-1.5 border-b border-[var(--hairline)] text-[10.5px] text-[var(--ink-muted)] uppercase tracking-wider font-semibold">
            Test Identities
          </div>
          <div className="pt-1.5 space-y-1">
            <button
              type="button"
              onClick={() => handleDevLogin("developer-personal", [12345])}
              className="w-full text-left px-3 py-1.5 hover:bg-[var(--canvas)] transition-colors flex items-center justify-between"
            >
              <span>Personal Org</span>
              <span className="text-[10px] text-[var(--ink-muted)]">#12345</span>
            </button>
            <button
              type="button"
              onClick={() => handleDevLogin("alice-security", [11111])}
              className="w-full text-left px-3 py-1.5 hover:bg-[var(--canvas)] transition-colors flex items-center justify-between"
            >
              <span>Alice</span>
              <span className="text-[10px] text-[var(--ink-muted)]">#11111</span>
            </button>
            <button
              type="button"
              onClick={() => handleDevLogin("bob-enterprise", [22222])}
              className="w-full text-left px-3 py-1.5 hover:bg-[var(--canvas)] transition-colors flex items-center justify-between"
            >
              <span>Bob</span>
              <span className="text-[10px] text-[var(--ink-muted)]">#22222</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
