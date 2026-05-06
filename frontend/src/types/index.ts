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

export interface Priority {
  id: string;
  label: string;
  description: string;
  icon: string;
}

export interface Course {
  title: string;
  platform: string;
  duration: string;
  url: string;
}

export interface SkillGap {
  name: string;
  current: SkillLevel;
  target: SkillLevel;
  progress: number;
  courses: Course[];
}

export interface CareerRecommendation {
  id: string;
  rank: number;
  title: string;
  description: string;
  avgSalary: string;
  growth: string;
  matchScore: number;
  skillGaps: SkillGap[];
}
