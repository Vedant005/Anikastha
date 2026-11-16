import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { AuthConfig, User } from "@/lib/types";
import { safeLocalStorage } from "@/lib/storage";
import {
  fetchAuthConfig as apiFetchAuthConfig,
  exchangeOAuthCode,
  fetchCurrentUser,
  devLogin as apiDevLogin,
} from "@/lib/api";

interface AuthStoreState {
  token: string | null;
  user: User | null;
  authConfig: AuthConfig | null;
  isLoading: boolean;
  error: string | null;
  showConsoleDemo: boolean;
  hasHydrated: boolean;

  setShowConsoleDemo: (show: boolean) => void;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setHasHydrated: (hydrated: boolean) => void;
  logout: () => void;
  fetchAuthConfig: () => Promise<void>;
  exchangeCode: (code: string) => Promise<User>;
  devLogin: (username?: string, installationIds?: number[]) => Promise<User>;
  checkSession: () => Promise<void>;
}

export const useAuthStore = create<AuthStoreState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      authConfig: null,
      isLoading: false,
      error: null,
      showConsoleDemo: false,
      hasHydrated: false,

      setShowConsoleDemo: (show: boolean) => set({ showConsoleDemo: show }),
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      setHasHydrated: (hydrated: boolean) => set({ hasHydrated: hydrated }),

      logout: () => {
        set({ token: null, user: null, error: null, showConsoleDemo: false });
        safeLocalStorage.removeItem("anikastha_token");
        safeLocalStorage.removeItem("anikastha-store-v1");
        safeLocalStorage.removeItem("anikastha-auth-v1");
      },

      fetchAuthConfig: async () => {
        try {
          const config = await apiFetchAuthConfig();
          set({ authConfig: config });
        } catch (err: any) {
          console.warn(
            "Backend auth config unavailable, falling back to local dev mode:",
            err?.message,
          );
          set({
            authConfig: {
              oauth_configured: false,
              github_app_url: "https://github.com/apps/anikastha",
              is_dev_mode: true,
            },
          });
        }
      },

      exchangeCode: async (code: string) => {
        set({ isLoading: true, error: null });
        try {
          const res = await exchangeOAuthCode(code);
          set({
            token: res.access_token,
            user: res.user,
            isLoading: false,
            error: null,
          });
          safeLocalStorage.setItem("pr_sentinel_token", res.access_token);
          return res.user;
        } catch (err: any) {
          set({
            error: err.message || "OAuth exchange failed",
            isLoading: false,
          });
          throw err;
        }
      },

      devLogin: async (username = "demo-developer", installationIds = []) => {
        set({ isLoading: true, error: null });
        try {
          const res = await apiDevLogin(username, installationIds);
          set({
            token: res.access_token,
            user: res.user,
            isLoading: false,
            error: null,
          });
          safeLocalStorage.setItem("pr_sentinel_token", res.access_token);
          return res.user;
        } catch (err: any) {
          set({
            error: err.message || "Dev login failed",
            isLoading: false,
          });
          throw err;
        }
      },

      checkSession: async () => {
        const token = get().token;
        if (!token) return;

        try {
          const user = await fetchCurrentUser();
          set({ user, error: null });
        } catch (err: any) {
          // Token expired or invalid -> logout cleanly
          get().logout();
        }
      },
    }),
    {
      name: "anikastha-auth-v1",
      storage: createJSONStorage(() => safeLocalStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);
