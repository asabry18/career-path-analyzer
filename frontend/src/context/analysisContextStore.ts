import { createContext } from "react";
import type { AnalyzeResponse, Priority, Skill } from "../types";

export interface AnalysisState {
  skills: Skill[];
  priorities: Priority[];
  result: AnalyzeResponse | null;
  loading: boolean;
  error: string | null;

  setSkills: (skills: Skill[]) => void;
  setPriorities: (priorities: Priority[]) => void;
  runAnalysis: (threshold?: number) => Promise<boolean>;
  clearResult: () => void;
}

export const AnalysisContext = createContext<AnalysisState | null>(null);
