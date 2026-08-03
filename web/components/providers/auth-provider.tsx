"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { api, tokenStore } from "@/lib/api/client";
import type { LoginResponse } from "@/types/api";

interface AuthUser {
  id: string;
  full_name: string;
  role: string;
  email?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: AuthUser | null) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const USER_KEY = "wms.user";

function readStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Hydrate session from localStorage on mount.
    const stored = readStoredUser();
    if (stored && tokenStore.getAccessToken()) {
      setUserState(stored);
    }
    setIsLoading(false);
  }, []);

  const setUser = useCallback((next: AuthUser | null) => {
    setUserState(next);
    if (typeof window !== "undefined") {
      if (next) window.localStorage.setItem(USER_KEY, JSON.stringify(next));
      else window.localStorage.removeItem(USER_KEY);
    }
  }, []);

  const applyLogin = useCallback(
    (response: LoginResponse) => {
      tokenStore.setTokens(response.tokens);
      setUser({
        id: response.user_id,
        full_name: response.full_name,
        role: response.role,
      });
    },
    [setUser]
  );

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.login({ email, password });
      applyLogin(response);
    },
    [applyLogin]
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const response = await api.register({ email, password, full_name: fullName });
      applyLogin(response);
    },
    [applyLogin]
  );

  const logout = useCallback(async () => {
    try {
      await api.logout(tokenStore.getRefreshToken() ?? undefined);
    } catch {
      // Proceed with local logout even if the backend call fails.
    }
    tokenStore.clear();
    setUser(null);
    router.push("/login");
  }, [router, setUser]);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user && tokenStore.getAccessToken()),
      isLoading,
      login,
      register,
      logout,
      setUser,
    }),
    [user, isLoading, login, register, logout, setUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

