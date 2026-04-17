import type { Priority } from "../types";

export const DEFAULT_PRIORITIES: Priority[] = [
  {
    id: "salary",
    label: "Salary",
    description: "Prioritize higher earning potential",
    icon: "salary",
  },
  {
    id: "demand",
    label: "Market Demand",
    description: "Focus on in-demand careers with job availability",
    icon: "demand",
  },
  {
    id: "match",
    label: "Skill Match",
    description: "Align with your current skill set",
    icon: "match",
  },
  {
    id: "learn",
    label: "Easy to Learn",
    description: "Choose paths with shorter learning curves",
    icon: "learn",
  },
];
