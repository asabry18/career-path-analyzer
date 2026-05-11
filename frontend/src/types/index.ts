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

export interface CatalogSkill {
  id: number;
  name: string;
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

export interface FrameworkChoice {
  slotLabel: string;
  alternatives: string[];
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
  frameworkChoices: FrameworkChoice[];
}

// ── Backend API response types ──────────────────────────────────────

export interface SkillRef {
  skill_id: number;
  name: string;
}

export interface FrameworkSlot {
  slot_index: number;
  alternatives: SkillRef[];
}

export interface ApiCourse {
  course_id: number;
  title: string;
  provider: string;
  url: string;
  skills: SkillRef[];
}

export interface ApiRankedJob {
  rank: number;
  job_id: number;
  title: string;
  description: string;
  topsis_score: number;
  skill_match_score: number;
  avg_salary: number;
  demand_score: number;
  learning_effort: number;
  missing_skills: SkillRef[];
  optional_frameworks: FrameworkSlot[];
}

export interface ApiAhp {
  weights: Record<string, number>;
  lambda_max: number;
  consistency_ratio: number;
  consistency_ok: boolean;
}

export interface ApiLearningPlan {
  selected_courses: ApiCourse[];
  covered_skills: SkillRef[];
  uncovered_skills: SkillRef[];
  solver_status: string;
}

export interface AnalyzeResponse {
  ahp: ApiAhp;
  ranked_jobs: ApiRankedJob[];
  learning_plan: ApiLearningPlan;
  meta: {
    vocab_size: number;
    jobs_evaluated: number;
    jobs_after_threshold: number;
  };
}

export interface AnalyzeRequest {
  skills: { name: string; level: SkillLevel }[];
  priorities: string[];
  threshold: number;
}
