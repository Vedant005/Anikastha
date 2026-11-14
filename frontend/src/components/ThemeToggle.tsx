"use client";

import { useTheme } from "./ThemeProvider";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      type="button"
      className={`relative inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono border border-[var(--hairline)] rounded-sm bg-[var(--surface)] text-[var(--ink-secondary)] hover:text-[var(--ink-primary)] hover:border-[var(--ink-primary)] transition-colors ${className}`}
      title={theme === "light" ? "Switch to Carbon Dark" : "Switch to Warm Paper Light"}
      aria-label="Toggle paper / carbon theme"
    >
      {theme === "light" ? (
        <>
          <Moon className="w-3.5 h-3.5 stroke-[1.75]" />
          <span className="hidden sm:inline">CARBON</span>
        </>
      ) : (
        <>
          <Sun className="w-3.5 h-3.5 stroke-[1.75]" />
          <span className="hidden sm:inline">PAPER</span>
        </>
      )}
    </button>
  );
}
