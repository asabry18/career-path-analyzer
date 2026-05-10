import type { AnalyzeResponse, CareerRecommendation, SkillGap } from "../types";

export function mapResultToRecommendations(
  resp: AnalyzeResponse
): CareerRecommendation[] {
  const courseLookup = new Map<string, { title: string; provider: string; url: string }>();
  for (const c of resp.learning_plan.selected_courses) {
    for (const sk of c.skills) {
      courseLookup.set(sk.name.toLowerCase(), {
        title: c.title,
        provider: c.provider,
        url: c.url,
      });
    }
  }

  return resp.ranked_jobs.map((job) => {
    const gaps: SkillGap[] = job.missing_skills.map((ms) => {
      const matched = courseLookup.get(ms.name.toLowerCase());
      return {
        name: ms.name,
        current: "Beginner" as const,
        target: "Advanced" as const,
        progress: 0,
        courses: matched
          ? [{ title: matched.title, platform: matched.provider, duration: "", url: matched.url }]
          : [],
      };
    });

    for (const fw of job.optional_frameworks) {
      const altNames = fw.alternatives.map((a) => a.name).join(" / ");
      const anyMatched = fw.alternatives.find((a) =>
        courseLookup.has(a.name.toLowerCase())
      );
      const courses = anyMatched
        ? (() => {
            const c = courseLookup.get(anyMatched.name.toLowerCase())!;
            return [{ title: c.title, platform: c.provider, duration: "", url: c.url }];
          })()
        : [];

      gaps.push({
        name: `Framework: ${altNames}`,
        current: "Beginner" as const,
        target: "Intermediate" as const,
        progress: 0,
        courses,
      });
    }

    return {
      id: String(job.job_id),
      rank: job.rank,
      title: job.title,
      description: job.description,
      avgSalary: `${job.avg_salary.toLocaleString()}K EGP`,
      growth: `Demand: ${job.demand_score}`,
      matchScore: Math.round(job.topsis_score * 100),
      skillGaps: gaps,
    };
  });
}
