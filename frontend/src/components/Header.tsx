import Link from "next/link";
import { Shield, GitPullRequest, Settings } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Shield className="h-6 w-6 text-white" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-100 tracking-tight">PR-Sentinel</span>
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
              AI Security
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link
            href="/"
            className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <GitPullRequest className="h-4 w-4 text-cyan-400" />
            Reviews
          </Link>
          <Link
            href="/repositories"
            className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <Settings className="h-4 w-4 text-blue-400" />
            Repositories & Policy
          </Link>
        </nav>
      </div>
    </header>
  );
}
