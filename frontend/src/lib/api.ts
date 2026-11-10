import { Policy, Repository, ReviewRun } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function fetchReviews(repoId?: string, limit: number = 20): Promise<ReviewRun[]> {
  const url = new URL(`${API_BASE}/reviews`);
  if (repoId) url.searchParams.set("repo_id", repoId);
  url.searchParams.set("limit", limit.toString());

  const res = await fetch(url.toString(), { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch reviews: ${res.statusText}`);
  return res.json();
}

export async function fetchReviewById(reviewId: string): Promise<ReviewRun> {
  const res = await fetch(`${API_BASE}/reviews/${reviewId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch review ${reviewId}: ${res.statusText}`);
  return res.json();
}

export async function rerunReview(reviewId: string): Promise<{ status: string; run_id: string }> {
  const res = await fetch(`${API_BASE}/reviews/${reviewId}/rerun`, { method: "POST" });
  if (!res.ok) throw new Error(`Failed to trigger rerun for ${reviewId}: ${res.statusText}`);
  return res.json();
}

export async function fetchRepositories(): Promise<Repository[]> {
  const res = await fetch(`${API_BASE}/repositories`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch repositories: ${res.statusText}`);
  return res.json();
}

export async function fetchRepositoryPolicy(repoId: string): Promise<Policy> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/policy`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch policy for ${repoId}: ${res.statusText}`);
  return res.json();
}

export async function updateRepositoryPolicy(
  repoId: string,
  policy: Partial<Policy>
): Promise<Policy> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/policy`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error(`Failed to update policy for ${repoId}: ${res.statusText}`);
  return res.json();
}
