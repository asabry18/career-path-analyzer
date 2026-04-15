export interface Career {
  id: number;
  title: string;
  salary: number;
  growth: number;
  openings: number;
}

export interface Stats {
  openingPositions: string;
  averageSalary: string;
  growthRate: string; 
}

export interface CareerData {
  topCareers: Career[];
  stats: Stats;
}

export type SkillLevel = "Beginner" | "Intermediate" | "Advanced";

export interface Skill {
  name: string;
  level: SkillLevel;
}
