import { useMemo, useState } from "react";
import type { InsightsJob } from "../../types";

const SECTOR_COLORS: Record<string, string> = {
  Software: "bg-blue-500",
  Network: "bg-emerald-500",
  Data: "bg-violet-500",
  Business: "bg-amber-500",
  Design: "bg-pink-500",
};

interface DemandSalaryChartProps {
  jobs: InsightsJob[];
}

function primarySector(sector?: string | null): string {
  if (!sector) return "Other";
  return sector.split(",")[0]?.trim() || "Other";
}

export default function DemandSalaryChart({ jobs }: DemandSalaryChartProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const { maxDemand, maxSalary, minSalary } = useMemo(() => {
    if (!jobs.length) {
      return { maxDemand: 1, maxSalary: 1, minSalary: 0 };
    }
    const salaries = jobs.map((job) => job.avg_salary);
    return {
      maxDemand: Math.max(...jobs.map((job) => job.demand_score), 1),
      maxSalary: Math.max(...salaries),
      minSalary: Math.min(...salaries),
    };
  }, [jobs]);

  if (!jobs.length) return null;

  const salaryRange = maxSalary - minSalary || 1;

  return (
    <section className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
        Demand vs Salary
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-6">
        Find sweet-spot careers — high demand and strong pay. Dot size reflects skill requirements.
      </p>

      <div className="relative h-64 sm:h-72 border-l border-b border-gray-200 dark:border-gray-700 ml-8 mb-2">
        <div className="absolute -left-8 top-1/2 -translate-y-1/2 -rotate-90 text-xs text-gray-400 whitespace-nowrap">
          Avg salary (K)
        </div>
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-6 text-xs text-gray-400">
          Market demand
        </div>

        {jobs.map((job) => {
          const left = `${(job.demand_score / maxDemand) * 100}%`;
          const bottom = `${((job.avg_salary - minSalary) / salaryRange) * 100}%`;
          const size = Math.max(8, Math.min(20, (job.skill_count ?? 5) * 1.2));
          const sector = primarySector(job.sector);
          const color = SECTOR_COLORS[sector] ?? "bg-gray-500";
          const isHovered = hoveredId === job.id;

          return (
            <div
              key={job.id}
              className="absolute -translate-x-1/2 translate-y-1/2 cursor-pointer"
              style={{ left, bottom }}
              onMouseEnter={() => setHoveredId(job.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              {isHovered && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap z-10 bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 shadow-lg">
                  <p className="capitalize">{job.title}</p>
                  <p>{job.demand_score} demand · {job.avg_salary.toFixed(1)}K</p>
                  {job.skill_count != null && <p>{job.skill_count} skills required</p>}
                </div>
              )}
              <span
                className={`block rounded-full ${color} ${isHovered ? "ring-2 ring-offset-2 ring-gray-400 dark:ring-gray-500" : ""}`}
                style={{ width: size, height: size }}
              />
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-3 mt-8 text-xs text-gray-500 dark:text-gray-400">
        {Object.entries(SECTOR_COLORS).map(([name, color]) => (
          <span key={name} className="inline-flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
            {name}
          </span>
        ))}
      </div>
    </section>
  );
}
