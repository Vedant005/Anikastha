import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { Repository, ReviewRun } from "@/lib/types";
import { fetchRepositories, fetchReviews } from "../lib/api";

export interface LoadDataOptions {
  silent?: boolean;
  force?: boolean;
}

interface ReviewStoreState {
  repositories: Repository[];
  reviews: ReviewRun[];
  selectedRepoId: string | null;
  isLoading: boolean;
  isRevalidating: boolean;
  hasHydrated: boolean;
  lastSyncedAt: number | null;
  error: string | null;

  loadInitialData: (options?: LoadDataOptions) => Promise<void>;
  setSelectedRepoId: (repoId: string | null) => void;
  updateReviewInList: (
    updatedReview: Partial<ReviewRun> & { id: string },
  ) => void;
  setHasHydrated: (hydrated: boolean) => void;
}

export const useReviewStore = create<ReviewStoreState>()(
  persist(
    (set, get) => ({
      repositories: [],
      reviews: [],
      selectedRepoId: null,
      isLoading: false,
      isRevalidating: false,
      hasHydrated: false,
      lastSyncedAt: null,
      error: null,

      setHasHydrated: (hydrated: boolean) => {
        set({ hasHydrated: hydrated });
      },

      loadInitialData: async (options = {}) => {
        const { silent = false, force = false } = options;
        const currentRepos = get().repositories;
        const currentReviews = get().reviews;
        const hasCachedData =
          currentRepos.length > 0 || currentReviews.length > 0;

        // If we don't have any cached data yet and this isn't a silent revalidation, show initial loader
        if (!hasCachedData && !silent) {
          set({ isLoading: true, error: null });
        } else {
          // If we have cached data, background revalidate without hiding UI content
          set({ isRevalidating: true, error: null });
        }

        try {
          const selectedRepoId = get().selectedRepoId;
          const [repos, revs] = await Promise.all([
            fetchRepositories(force),
            fetchReviews(selectedRepoId || undefined, 20, force),
          ]);

          set({
            repositories: repos,
            reviews: revs,
            isLoading: false,
            isRevalidating: false,
            lastSyncedAt: Date.now(),
            error: null,
          });
        } catch (err: any) {
          // Preserve cached content on network failure
          set({
            error: err.message || "Failed to update dashboard data",
            isLoading: false,
            isRevalidating: false,
          });
        }
      },

      setSelectedRepoId: (repoId: string | null) => {
        set({ selectedRepoId: repoId, isRevalidating: true });
        fetchReviews(repoId || undefined)
          .then((revs) =>
            set({
              reviews: revs,
              isRevalidating: false,
              lastSyncedAt: Date.now(),
            })
          )
          .catch((err) =>
            set({ error: err.message, isRevalidating: false })
          );
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
    }),
    {
      name: "pr-sentinel-store-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        repositories: state.repositories,
        reviews: state.reviews,
        selectedRepoId: state.selectedRepoId,
        lastSyncedAt: state.lastSyncedAt,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
