import type {
  AnalyzeResponse,
  CareerRecommendation,
  FrameworkChoice,
  SkillGap,
} from "../types";

export function mapResultToRecommendations(
  resp: AnalyzeResponse
): CareerRecommendation[] {
  const courseLookup = new Map<
    string,
    { title: string; provider: string; url: string }
  >();
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
          ? [
              {
                title: matched.title,
                platform: matched.provider,
                duration: "",
                url: matched.url,
              },
            ]
          : [],
      };
    });

    const frameworkChoices: FrameworkChoice[] = job.optional_frameworks.map(
      (fw) => ({
        slotLabel: `Framework Slot ${fw.slot_index + 1}`,
        alternatives: fw.alternatives.map((a) => a.name),
      })
    );

    return {
      id: String(job.job_id),
      rank: job.rank,
      title: job.title,
      description: job.description,
      avgSalary: `${job.avg_salary.toLocaleString()}K EGP`,
      growth: `Demand: ${job.demand_score}`,
      matchScore: Math.round(job.topsis_score * 100),
      skillGaps: gaps,
      frameworkChoices,
    };
  });
}
