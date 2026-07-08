import axios from "axios";
import type {
  AnalyzeRequest,
  AnalyzeResponse,
  AuthTokens,
  AuthUser,
  CatalogSkill,
  InsightsResponse,
  LoginRequest,
  SignupRequest,
  SignupResponse,
} from "../types";

const ACCESS_KEY = "career_path_access";
const REFRESH_KEY = "career_path_refresh";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
  headers: { "Content-Type": "application/json" },
});

export function setAuthToken(token?: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

// ---------------------------------------------------------------------------
// Silent token-refresh interceptor
// When any request returns 401, try to get a new access token using the
// stored refresh token and replay the original request exactly once.
// Only if the refresh itself fails do we clear the session (logout).
// ---------------------------------------------------------------------------
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only handle 401s that haven't already been retried,
    // and skip the refresh endpoint itself to avoid infinite loops.
    if (
      error?.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes("/auth/refresh/")
    ) {
      const refreshToken = localStorage.getItem(REFRESH_KEY);

      if (!refreshToken) {
        // No refresh token stored — clear session and reject.
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        setAuthToken(null);
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Another request is already refreshing — queue this one.
        return new Promise((resolve) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post<{ access: string; refresh?: string }>(
          `${api.defaults.baseURL}/auth/refresh/`,
          { refresh: refreshToken },
          { headers: { "Content-Type": "application/json" } }
        );

        const newAccess = data.access;
        // If the backend rotates refresh tokens, persist the new one.
        if (data.refresh) {
          localStorage.setItem(REFRESH_KEY, data.refresh);
        }
        localStorage.setItem(ACCESS_KEY, newAccess);
        setAuthToken(newAccess);

        onRefreshed(newAccess);
        originalRequest.headers.Authorization = `Bearer ${newAccess}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed — clear everything so the user is sent to login.
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        setAuthToken(null);
        refreshSubscribers = [];
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export async function fetchSkills(): Promise<CatalogSkill[]> {
  const { data } = await api.get<CatalogSkill[]>("/skills/");
  return data;
}

export async function analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/analyze/", req);
  return data;
}

export async function signup(req: SignupRequest): Promise<SignupResponse> {
  const { data } = await api.post<SignupResponse>("/auth/signup/", req);
  return data;
}

export async function login(req: LoginRequest): Promise<AuthTokens> {
  const { data } = await api.post<AuthTokens>("/auth/login/", req);
  return data;
}

export async function refreshTokenCall(refresh: string): Promise<{ access: string }> {
  const { data } = await api.post<{ access: string }>("/auth/refresh/", { refresh });
  return data;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await api.get<AuthUser>("/auth/me/");
  return data;
}

export async function fetchInsights(): Promise<InsightsResponse> {
  const { data } = await api.get<InsightsResponse>("/insights/");
  return data;
}
