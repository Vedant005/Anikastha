import { AuthConfig, Policy, Repository, ReviewRun, User } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const raw = localStorage.getItem("pr_sentinel_token");
    if (raw) {
      return { Authorization: `Bearer ${raw}` };
    }
    const zustandAuth = localStorage.getItem("pr-sentinel-auth-v1");
    if (zustandAuth) {
      const parsed = JSON.parse(zustandAuth);
      if (parsed?.state?.token) {
        return { Authorization: `Bearer ${parsed.state.token}` };
      }
    }
  } catch {
    // Ignore JSON parse errors in localStorage
  }
  return {};
}

// Authentication Endpoints
export async function fetchAuthConfig(): Promise<AuthConfig> {
  const res = await fetch(`${API_BASE}/auth/config`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch auth configuration");
  return res.json();
}

export async function getGitHubLoginUrl(): Promise<string> {
  const res = await fetch(`${API_BASE}/auth/github/login-url`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error("GitHub OAuth is not configured on the server");
  const data = await res.json();
  return data.url;
}

export async function exchangeOAuthCode(
  code: string,
): Promise<{ access_token: string; token_type: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `OAuth exchange failed: ${res.statusText}`);
  }
  return res.json();
}

export async function devLogin(
  username: string = "demo-developer",
  installationIds: number[] = [],
): Promise<{ access_token: string; token_type: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/dev-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      installation_ids: installationIds,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Dev login failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchCurrentUser(): Promise<User> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: { ...headers },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Unauthorized or session expired`);
  return res.json();
}

// Reviews & Repositories Endpoints
export async function fetchReviews(
  repoId?: string,
  limit: number = 20,
  forceRefresh: boolean = false,
): Promise<ReviewRun[]> {
  const url = new URL(`${API_BASE}/reviews`);
  if (repoId) url.searchParams.set("repo_id", repoId);
  url.searchParams.set("limit", limit.toString());

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), {
    headers: { ...headers },
    cache: forceRefresh ? "no-store" : "default",
  });
  if (!res.ok) throw new Error(`Failed to fetch reviews: ${res.statusText}`);
  return res.json();
}

export async function fetchReviewById(
  reviewId: string,
  forceRefresh: boolean = false,
): Promise<ReviewRun> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/reviews/${reviewId}`, {
    headers: { ...headers },
    cache: forceRefresh ? "no-store" : "default",
  });
  if (!res.ok)
    throw new Error(`Failed to fetch review ${reviewId}: ${res.statusText}`);
  return res.json();
}

export async function rerunReview(
  reviewId: string,
): Promise<{ status: string; run_id: string }> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/reviews/${reviewId}/rerun`, {
    method: "POST",
    headers: { ...headers },
  });
  if (!res.ok)
    throw new Error(
      `Failed to trigger rerun for ${reviewId}: ${res.statusText}`,
    );
  return res.json();
}

export async function fetchRepositories(
  forceRefresh: boolean = false,
): Promise<Repository[]> {
  const headers = getAuthHeaders();
  const url = new URL(`${API_BASE}/repositories`);
  if (forceRefresh) {
    url.searchParams.set("sync", "true");
  }
  const res = await fetch(url.toString(), {
    headers: { ...headers },
    cache: forceRefresh ? "no-store" : "default",
  });
  if (!res.ok)
    throw new Error(`Failed to fetch repositories: ${res.statusText}`);
  return res.json();
}

export async function syncRepositories(): Promise<Repository[]> {
  const headers = getAuthHeaders();
  try {
    const res = await fetch(`${API_BASE}/repositories/sync`, {
      method: "POST",
      headers: { ...headers },
    });
    if (res.ok) {
      return res.json();
    }
  } catch {
    // fallback
  }
  return fetchRepositories(true);
}

export async function fetchRepositoryPolicy(
  repoId: string,
  forceRefresh: boolean = false,
): Promise<Policy> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/repositories/${repoId}/policy`, {
    headers: { ...headers },
    cache: forceRefresh ? "no-store" : "default",
  });
  if (!res.ok)
    throw new Error(`Failed to fetch policy for ${repoId}: ${res.statusText}`);
  return res.json();
}

export async function updateRepositoryPolicy(
  repoId: string,
  policy: Partial<Policy>,
): Promise<Policy> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_BASE}/repositories/${repoId}/policy`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: JSON.stringify(policy),
  });
  if (!res.ok)
    throw new Error(`Failed to update policy for ${repoId}: ${res.statusText}`);
  return res.json();
}
