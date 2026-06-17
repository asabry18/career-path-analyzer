import { useEffect, useMemo, useState } from "react";
import PageLayout from "../../components/PageLayout";
import Hero from "../../components/Hero";
import StatsCards from "../../components/StatsCards";
import SectorInsights from "../../components/SectorInsights";
import PrioritySpotlights from "../../components/PrioritySpotlights";
import HighLeverageSkills from "../../components/HighLeverageSkills";
import DemandSalaryChart from "../../components/DemandSalaryChart";
import { fetchInsights } from "../../api/client";
import type { InsightsResponse, Stats } from "../../types";

export default function HomePage() {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    fetchInsights()
      .then((data) => {
        if (active) setInsights(data);
      })
      .catch(() => {
        if (active) setError("Unable to load insights right now.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const stats: Stats | null = useMemo(() => {
    if (!insights) return null;
    return {
      jobCount: insights.job_count.toLocaleString(),
      medianSalary: `${insights.median_salary.toFixed(1)}K EGP`,
      salaryIqr: `${insights.salary_iqr.toFixed(1)}K`,
    };
  }, [insights]);

  return (
    <PageLayout>
      <main>
        <Hero />
        {loading && (
          <div className="max-w-5xl mx-auto px-4 py-10">
            <p className="text-sm text-gray-500 dark:text-gray-400">Loading insights...</p>
          </div>
        )}

        {error && (
          <div className="max-w-5xl mx-auto px-4 py-6">
            <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-5 py-3">
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          </div>
        )}

        {stats && <StatsCards stats={stats} />}

        {insights && (
          <div className="max-w-5xl mx-auto px-4 pb-10 space-y-10">
            {insights.priority_spotlights && (
              <PrioritySpotlights spotlights={insights.priority_spotlights} />
            )}

            {insights.sectors?.length > 0 && (
              <SectorInsights
                sectors={insights.sectors}
                entryRolesBySector={insights.entry_roles_by_sector ?? []}
              />
            )}

            {insights.demand_salary_jobs?.length > 0 && (
              <DemandSalaryChart jobs={insights.demand_salary_jobs} />
            )}

            {insights.high_leverage_skills?.length > 0 && (
              <HighLeverageSkills
                skills={insights.high_leverage_skills}
                jobCount={insights.job_count}
              />
            )}
          </div>
        )}
      </main>
    </PageLayout>
  );
}
