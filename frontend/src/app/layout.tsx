import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/Header";

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
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600">
          PR-Sentinel &copy; 2026 &bull; Multi-Agent AI Security Code Reviewer
        </footer>
      </body>
    </html>
  );
}
