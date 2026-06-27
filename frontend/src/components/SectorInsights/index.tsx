import { Briefcase, TrendingUp, DollarSign } from "lucide-react";
import type { InsightsEntryRolesBySector, InsightsSector } from "../../types";

const SECTOR_DESCRIPTIONS: Record<string, string> = {
  Software: "Build applications, design user experiences, and grow product-focused careers.",
  Network: "Maintain infrastructure, security, and IT operations.",
  Data: "Analyze, engineer, and model data for business insights.",
};

const SECTOR_CHOOSE_IF: Record<string, string> = {
  Software:
    "Choose this if you enjoy building products, designing interfaces, or working in tech-enabled roles.",
  Network: "Choose this if you prefer systems, troubleshooting, and infrastructure.",
  Data: "Choose this if you like working with numbers, patterns, and insights.",
};

const SECTOR_COLORS: Record<string, string> = {
  Software: "bg-blue-500",
  Network: "bg-emerald-500",
  Data: "bg-violet-500",
};

interface SectorInsightsProps {
  sectors: InsightsSector[];
  entryRolesBySector: InsightsEntryRolesBySector[];
}

export default function SectorInsights({ sectors, entryRolesBySector }: SectorInsightsProps) {
  if (!sectors.length) return null;

  const demandMax = Math.max(...sectors.map((sector) => sector.total_demand), 1);
  const entryMap = Object.fromEntries(
    entryRolesBySector.map((group) => [group.sector, group.roles])
  );

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Explore Market Sectors
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Compare sectors and find beginner-friendly entry roles in each path.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sectors.map((sector) => {
          const barColor = SECTOR_COLORS[sector.name] ?? "bg-gray-700 dark:bg-gray-300";
          const description =
            SECTOR_DESCRIPTIONS[sector.name] ?? "Roles aligned with this market sector.";
          const chooseIf =
            SECTOR_CHOOSE_IF[sector.name] ?? "Explore roles that match your interests.";
          const entryRoles = entryMap[sector.name] ?? [];

          return (
            <article
              key={sector.name}
              className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="text-base font-semibold text-gray-900 dark:text-white">
                    {sector.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{description}</p>
                </div>
                <span
                  className={`shrink-0 w-3 h-3 rounded-full mt-1.5 ${barColor}`}
                  aria-hidden
                />
              </div>

              <p className="text-xs text-primary mt-3">{chooseIf}</p>

              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="flex items-center gap-2">
                  <Briefcase size={14} className="text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-400">Jobs</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {sector.job_count}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign size={14} className="text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-400">Avg salary</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {sector.avg_salary.toFixed(1)}K
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp size={14} className="text-gray-400" />
                  <div>
                    <p className="text-xs text-gray-400">Demand</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {sector.total_demand}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-4">
                <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-800">
                  <div
                    className={`h-2 rounded-full ${barColor}`}
                    style={{ width: `${(sector.total_demand / demandMax) * 100}%` }}
                  />
                </div>
              </div>

              {entryRoles.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-300 mb-2">
                    Good starting points
                  </p>
                  <ul className="space-y-2">
                    {entryRoles.map((role) => (
                      <li key={role.id} className="text-xs text-gray-500 dark:text-gray-400">
                        <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">
                          {role.title}
                        </span>
                        {role.key_skills && role.key_skills.length > 0 && (
                          <span className="block mt-0.5">
                            {role.key_skills.join(", ")}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
