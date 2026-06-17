import { useCallback, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import type { AuthTokens, AuthUser, LoginRequest, SignupRequest } from "../types";
import { fetchMe, login as loginApi, setAuthToken, signup as signupApi, refreshTokenCall } from "../api/client";
import { AuthContext } from "./authContextStore";

const ACCESS_KEY = "career_path_access";
const REFRESH_KEY = "career_path_refresh";

function loadTokens(): AuthTokens | null {
  const access = localStorage.getItem(ACCESS_KEY);
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!access || !refresh) return null;
  return { access, refresh };
}

function saveTokens(tokens: AuthTokens | null) {
  if (tokens) {
    localStorage.setItem(ACCESS_KEY, tokens.access);
    localStorage.setItem(REFRESH_KEY, tokens.refresh);
  } else {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [tokens, setTokens] = useState<AuthTokens | null>(() => loadTokens());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tokens?.access) {
      setAuthToken(tokens.access);
    }
  }, [tokens]);

  useEffect(() => {
    let active = true;
    if (!tokens?.access) {
      setUser(null);
      return undefined;
    }

    setLoading(true);
    fetchMe()
      .then((me) => {
        if (active) setUser(me);
      })
      .catch(async (err: any) => {
        if (!active) return;
        
        // If it's a 401, try to refresh the token
        if (err?.response?.status === 401 && tokens?.refresh) {
          try {
            const res = await refreshTokenCall(tokens.refresh);
            const newTokens = { access: res.access, refresh: tokens.refresh };
            setTokens(newTokens);
            saveTokens(newTokens);
            setAuthToken(res.access);
            
            const me = await fetchMe();
            if (active) setUser(me);
            return;
          } catch (refreshErr) {
            // refresh failed, clear tokens
          }
        }
        
        // For other errors (or if refresh failed), log out if it's an auth error.
        // If it's a network error (no response), keep the user session locally.
        if (active && err?.response) {
          setUser(null);
          setTokens(null);
          saveTokens(null);
          setAuthToken(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [tokens?.access, tokens?.refresh]);

  const handleTokens = useCallback((next: AuthTokens) => {
    setTokens(next);
    saveTokens(next);
    setAuthToken(next.access);
  }, []);

  const login = useCallback(async (req: LoginRequest) => {
    setLoading(true);
    setError(null);
    try {
      const nextTokens = await loginApi(req);
      handleTokens(nextTokens);
      const me = await fetchMe();
      setUser(me);
      return true;
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Login failed");
      }
      return false;
    } finally {
      setLoading(false);
    }
  }, [handleTokens]);

  const signup = useCallback(async (req: SignupRequest) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await signupApi(req);
      handleTokens({ access: resp.access, refresh: resp.refresh });
      setUser(resp.user);
      return true;
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Signup failed");
      }
      return false;
    } finally {
      setLoading(false);
    }
  }, [handleTokens]);

  const logout = useCallback(() => {
    setUser(null);
    setTokens(null);
    saveTokens(null);
    setAuthToken(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      tokens,
      loading,
      error,
      login,
      signup,
      logout,
    }),
    [user, tokens, loading, error, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
