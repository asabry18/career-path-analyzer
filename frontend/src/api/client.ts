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
