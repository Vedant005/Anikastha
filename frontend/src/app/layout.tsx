import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "PR-Sentinel | Autonomous GitHub Security Reviewer",
  description: "Autonomous AI-Powered GitHub Pull Request security reviewer dashboard.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col lg:flex-row bg-[var(--canvas)] text-[var(--ink-primary)] antialiased">
        <ThemeProvider>
          {/* Two-pane App Shell: Fixed ~240px Paper Sidebar */}
          <Sidebar />

          {/* Main Column Stacking Header and Content */}
          <div className="flex-1 flex flex-col min-w-0 min-h-screen">
            {children}
            <footer className="mt-auto border-t border-[var(--hairline)] px-6 py-4 text-center text-[10px] font-mono text-[var(--ink-muted)] flex flex-wrap items-center justify-between gap-2">
              <span>PR-Sentinel &bull; Multi-Agent Security Reviewer</span>
              <span>IBM Plex Mono &bull; E-Ink Architecture</span>
              <span>HMAC SHA-256 &bull; LangGraph Pipeline</span>
            </footer>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
