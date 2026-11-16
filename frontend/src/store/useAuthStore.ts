import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { AuthConfig, User } from "@/lib/types";
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

  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
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

      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),

      logout: () => {
        set({ token: null, user: null, error: null });
        if (typeof window !== "undefined") {
          localStorage.removeItem("pr_sentinel_token");
        }
      },

      fetchAuthConfig: async () => {
        try {
          const config = await apiFetchAuthConfig();
          set({ authConfig: config });
        } catch (err: any) {
          console.warn("Failed to fetch auth config:", err);
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
          if (typeof window !== "undefined") {
            localStorage.setItem("pr_sentinel_token", res.access_token);
          }
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
          if (typeof window !== "undefined") {
            localStorage.setItem("pr_sentinel_token", res.access_token);
          }
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
          // Token expired or invalid -> logout
          get().logout();
        }
      },
    }),
    {
      name: "pr-sentinel-auth-v1",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        token: state.token,
        user: state.user,
      }),
    }
  )
);
