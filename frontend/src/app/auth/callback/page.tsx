"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { useReviewStore } from "@/store/useReviewStore";
import { AlertCircle, Loader2 } from "lucide-react";
import Link from "next/link";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { exchangeCode } = useAuthStore();
  const { loadInitialData } = useReviewStore();

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const ghError = searchParams.get("error_description") || searchParams.get("error");

    if (ghError) {
      setError(ghError);
      return;
    }

    if (!code) {
      setError("No authorization code provided by GitHub.");
      return;
    }

    let isMounted = true;

    async function handleExchange() {
      try {
        await exchangeCode(code!);
        if (isMounted) {
          // Immediately reload reviews and repositories for the newly authenticated user
          await loadInitialData({ force: true });
          router.replace("/");
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to complete authentication with GitHub.");
        }
      }
    }

    handleExchange();

    return () => {
      isMounted = false;
    };
  }, [searchParams, exchangeCode, loadInitialData, router]);

  if (error) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-md w-full p-6 border border-[var(--hairline)] bg-[var(--surface)] rounded-sm space-y-4 font-mono text-xs">
          <div className="flex items-center justify-center text-[var(--signal-red)]">
            <AlertCircle className="w-8 h-8 stroke-[1.5]" />
          </div>
          <div className="space-y-1">
            <h2 className="text-sm font-semibold text-[var(--ink-primary)]">
              Authentication Failed
            </h2>
            <p className="text-[var(--ink-secondary)]">{error}</p>
          </div>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-flex items-center justify-center px-4 py-2 border border-[var(--ink-primary)] bg-[var(--ink-primary)] text-[var(--canvas)] rounded-xs hover:opacity-90 transition-opacity font-medium"
            >
              Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center font-mono">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="w-6 h-6 animate-spin text-[var(--ink-primary)] stroke-[1.5]" />
        <p className="text-xs text-[var(--ink-secondary)]">
          Authenticating with GitHub & synchronizing repositories...
        </p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[50vh] flex items-center justify-center font-mono text-xs text-[var(--ink-muted)]">
          Loading authentication status...
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
