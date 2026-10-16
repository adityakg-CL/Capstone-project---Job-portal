// Auth session state. The backend is the authority for identity and role.
// Frontend role toggle was demo-only and is not trusted for authorization.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, getStoredUser, getToken, setSession, type ApiUser, type BackendRole } from "../services/api";

export type UiRole = "employee" | "manager";

export function toUiRole(role: BackendRole): UiRole {
  return role === "employee" ? "employee" : "manager";
}

/** Human label for a backend role, shown in the UI badge. */
export function roleLabel(role: BackendRole): string {
  if (role === "hr_admin") return "HR Admin";
  if (role === "hiring_manager") return "Hiring Manager";
  return "Employee";
}

/**
 * Avatar initials derived from the actual account name.
 * Falls back to the first letter of the email local-part, then to a neutral
 * marker. Never a hardcoded person.
 */
export function initialsFor(name?: string | null, email?: string | null): string {
  const source = (name ?? "").trim() || (email ?? "").trim().split("@")[0].replace(/[._-]+/g, " ");
  const parts = source.split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

interface AuthState {
  user: ApiUser | null;
  uiRole: UiRole;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<ApiUser>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  /** Merge a freshly-saved profile into session state so every screen agrees. */
  applyUser: (next: ApiUser) => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  // The cached user is only a first paint; refresh() below always re-reads the
  // real account from GET /auth/me, so a stale cache can never win.
  const [user, setUser] = useState<ApiUser | null>(() => getStoredUser());
  const [loading, setLoading] = useState<boolean>(Boolean(getToken()));
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const me = await api.fetchMe();
      setUser(me.user);
      setSession(getToken(), me.user);
    } catch (err) {
      // A token the server rejects clears the session entirely rather than
      // leaving a stale identity on screen.
      setSession(null, null);
      setUser(null);
      setError(err instanceof Error ? err.message : "Session expired. Please sign in again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    const result = await api.login({ email, password });
    setUser(result.user);
    return result.user;
  }, []);

  const register = useCallback(async (fullName: string, email: string, password: string) => {
    setError(null);
    await api.register({ full_name: fullName, email, password });
    // Registration returns only the user; sign in separately to obtain a token.
    const result = await api.login({ email, password });
    setUser(result.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      // Clear local state even if the server call fails, so no identity leaks
      // into the next session.
      setUser(null);
      setError(null);
    }
  }, []);

  const applyUser = useCallback((next: ApiUser) => {
    setUser(next);
    setSession(getToken(), next);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      uiRole: toUiRole(user?.role ?? "employee"),
      loading,
      error,
      login,
      register,
      logout,
      refresh,
      applyUser,
    }),
    [user, loading, error, login, register, logout, refresh, applyUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

