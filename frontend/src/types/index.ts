export interface Stats {
  jobCount: string;
  medianSalary: string;
  salaryIqr: string;
}

export type SkillLevel =
  | "Beginner"
  | "Under Average"
  | "Average"
  | "Above Average"
  | "Advanced";

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

// ── Auth types ─────────────────────────────────────────────────────

export interface AuthUser {
  first_name: string;
  last_name: string;
  email: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface SignupResponse extends AuthTokens {
  user: AuthUser;
}

// ── Insights types ────────────────────────────────────────────────

export interface InsightsJob {
  id: number;
  title: string;
  demand_score: number;
  avg_salary: number;
  sector?: string | null;
  skill_count?: number;
  salary_band?: string | null;
  key_skills?: string[];
}

export interface InsightsSkill {
  id: number;
  name: string;
  frequency: number;
}

export interface InsightsHighLeverageSkill {
  id: number;
  name: string;
  job_count: number;
  course_count: number;
}

export interface InsightsPrioritySpotlights {
  salary: InsightsJob[];
  demand: InsightsJob[];
  easy_entry: InsightsJob[];
  balance: InsightsJob[];
}

export interface InsightsEntryRolesBySector {
  sector: string;
  roles: InsightsJob[];
}

export interface InsightsCourse {
  id: number;
  title: string;
  provider: string;
  skill_count: number;
}

export interface InsightsProvider {
  provider: string;
  count: number;
}

export interface InsightsSector {
  name: string;
  job_count: number;
  total_demand: number;
  avg_salary: number;
  top_job: InsightsJob | null;
}

export interface InsightsResponse {
  job_count: number;
  median_salary: number;
  salary_iqr: number;
  top_demanded_jobs: InsightsJob[];
  top_salary_jobs: InsightsJob[];
  top_skills: InsightsSkill[];
  sectors: InsightsSector[];
  priority_spotlights: InsightsPrioritySpotlights;
  entry_roles_by_sector: InsightsEntryRolesBySector[];
  high_leverage_skills: InsightsHighLeverageSkill[];
  demand_salary_jobs: InsightsJob[];
  courses: {
    total_courses: number;
    top_courses: InsightsCourse[];
    top_providers: InsightsProvider[];
  };
}
