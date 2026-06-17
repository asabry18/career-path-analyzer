import { useContext } from "react";
import type { AnalysisState } from "./analysisContextStore";
import { AnalysisContext } from "./analysisContextStore";

export function useAnalysis(): AnalysisState {
  const ctx = useContext(AnalysisContext);
  if (!ctx)
    throw new Error("useAnalysis must be used within <AnalysisProvider>");
  return ctx;
}
