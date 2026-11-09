import { create } from "zustand";
import { Repository, ReviewRun } from "@/lib/types";
import { fetchRepositories, fetchReviews } from "../lib/api";

interface ReviewStoreState {
  repositories: Repository[];
  reviews: ReviewRun[];
  selectedRepoId: string | null;
  isLoading: boolean;
  error: string | null;

  loadInitialData: () => Promise<void>;
  setSelectedRepoId: (repoId: string | null) => void;
  updateReviewInList: (
    updatedReview: Partial<ReviewRun> & { id: string },
  ) => void;
}

export const useReviewStore = create<ReviewStoreState>((set, get) => ({
  repositories: [],
  reviews: [],
  selectedRepoId: null,
  isLoading: false,
  error: null,

  loadInitialData: async () => {
    set({ isLoading: true, error: null });
    try {
      const [repos, revs] = await Promise.all([
        fetchRepositories(),
        fetchReviews(),
      ]);
      set({ repositories: repos, reviews: revs, isLoading: false });
    } catch (err: any) {
      set({
        error: err.message || "Failed to load dashboard data",
        isLoading: false,
      });
    }
  },

  setSelectedRepoId: (repoId: string | null) => {
    set({ selectedRepoId: repoId });
    // Re-fetch reviews filtered by repo
    fetchReviews(repoId || undefined)
      .then((revs) => set({ reviews: revs }))
      .catch((err) => set({ error: err.message }));
  },

  updateReviewInList: (updated) => {
    const current = get().reviews;
    const idx = current.findIndex((r) => r.id === updated.id);
    if (idx !== -1) {
      const copy = [...current];
      copy[idx] = { ...copy[idx], ...updated };
      set({ reviews: copy });
    }
  },
}));
