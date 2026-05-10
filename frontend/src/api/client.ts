import axios from "axios";
import type { AnalyzeRequest, AnalyzeResponse, CatalogSkill } from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api",
  headers: { "Content-Type": "application/json" },
});

export async function fetchSkills(): Promise<CatalogSkill[]> {
  const { data } = await api.get<CatalogSkill[]>("/skills/");
  return data;
}

export async function analyze(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const { data } = await api.post<AnalyzeResponse>("/analyze/", req);
  return data;
}
