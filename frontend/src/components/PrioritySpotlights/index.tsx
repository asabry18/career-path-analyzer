import { useNavigate } from "react-router-dom";
import { DollarSign, TrendingUp, GraduationCap, Scale, ArrowRight } from "lucide-react";
import { useAuth } from "../../context/useAuth";
import type { InsightsJob, InsightsPrioritySpotlights } from "../../types";

const SPOTLIGHT_CONFIG = [
  {
    key: "salary" as const,
    title: "Highest Pay",
    description: "Roles with the strongest earning potential",
    Icon: DollarSign,
    accent: "text-emerald-500",
  },
  {
    key: "demand" as const,
    title: "Most In Demand",
    description: "Careers with the most job openings",
    Icon: TrendingUp,
    accent: "text-blue-500",
  },
  {
    key: "easy_entry" as const,
    title: "Easiest Entry",
    description: "Paths with fewer skills to get started",
    Icon: GraduationCap,
    accent: "text-violet-500",
  },
  {
    key: "balance" as const,
    title: "Best Balance",
    description: "Strong mix of pay, demand, and accessibility",
    Icon: Scale,
    accent: "text-amber-500",
  },
];

interface PrioritySpotlightsProps {
  spotlights: InsightsPrioritySpotlights;
}

function JobRow({
  job,
  variant,
}: {
  job: InsightsJob;
  variant: keyof InsightsPrioritySpotlights;
}) {
  const renderMetric = () => {
    switch (variant) {
      case "salary":
        return (
          <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-xs text-gray-500 dark:text-gray-400">
            <span>{job.avg_salary.toFixed(1)}K avg</span>
            {job.salary_band && <span>{job.salary_band}</span>}
          </div>
        );
      case "demand":
        return (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {job.demand_score} demand
          </p>
        );
      case "easy_entry":
        return (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {job.skill_count ?? "—"} skills required
          </p>
        );
      case "balance":
        return (
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {job.avg_salary.toFixed(1)}K avg · {job.demand_score} demand ·{" "}
            {job.skill_count ?? "—"} skills
          </p>
        );
      default:
        return null;
    }
  };

  return (
    <li className="rounded-lg bg-gray-50 dark:bg-gray-800/60 px-3 py-2.5">
      <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
        {job.title}
      </p>
      {renderMetric()}
    </li>
  );
}

export default function PrioritySpotlights({ spotlights }: PrioritySpotlightsProps) {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleStart = () => {
    navigate(user ? "/skills" : "/login");
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Choose What Matters to You
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Explore careers by the same priorities you will rank in your analysis.
          </p>
        </div>
        <button
          type="button"
          onClick={handleStart}
          className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:opacity-80"
        >
          Get personalized matches
          <ArrowRight size={16} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SPOTLIGHT_CONFIG.map(({ key, title, description, Icon, accent }) => {
          const jobs = spotlights[key];
          if (!jobs?.length) return null;

          return (
            <article
              key={key}
              className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5"
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon size={18} className={accent} />
                <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                  {title}
                </h3>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{description}</p>
              <ul className="space-y-2">
                {jobs.map((job) => (
                  <JobRow key={job.id} job={job} variant={key} />
                ))}
              </ul>
            </article>
          );
        })}
      </div>
    </section>
  );
}
