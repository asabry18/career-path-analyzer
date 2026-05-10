import { createContext, useContext, useState, useCallback } from "react";
import type { ReactNode } from "react";
import type { Skill, Priority, AnalyzeResponse } from "../types";
import { analyze } from "../api/client";
import { DEFAULT_PRIORITIES } from "../data/priorities";

interface AnalysisState {
  skills: Skill[];
  priorities: Priority[];
  result: AnalyzeResponse | null;
  loading: boolean;
  error: string | null;

  setSkills: (skills: Skill[]) => void;
  setPriorities: (priorities: Priority[]) => void;
  runAnalysis: (threshold?: number) => Promise<void>;
  clearResult: () => void;
}

const AnalysisContext = createContext<AnalysisState | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [priorities, setPriorities] = useState<Priority[]>(DEFAULT_PRIORITIES);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runAnalysis = useCallback(
    async (threshold = 0.1) => {
      setLoading(true);
      setError(null);
      setResult(null);

      try {
        const resp = await analyze({
          skills: skills.map((s) => ({ name: s.name, level: s.level })),
          priorities: priorities.map((p) => p.id),
          threshold,
        });
        setResult(resp);
      } catch (err: unknown) {
        if (
          err &&
          typeof err === "object" &&
          "response" in err &&
          (err as { response?: { data?: { detail?: string } } }).response?.data
            ?.detail
        ) {
          setError(
            (err as { response: { data: { detail: string } } }).response.data
              .detail
          );
        } else if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unexpected error occurred");
        }
      } finally {
        setLoading(false);
      }
    },
    [skills, priorities]
  );

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return (
    <AnalysisContext.Provider
      value={{
        skills,
        priorities,
        result,
        loading,
        error,
        setSkills,
        setPriorities,
        runAnalysis,
        clearResult,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis(): AnalysisState {
  const ctx = useContext(AnalysisContext);
  if (!ctx)
    throw new Error("useAnalysis must be used within <AnalysisProvider>");
  return ctx;
}
