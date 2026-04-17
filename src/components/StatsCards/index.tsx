import { Building2, DollarSign, TrendingUp } from "lucide-react";
import type { Stats } from "../../types";

interface StatsCardsProps {
  stats: Stats;
}

const iconMap = [
  { key: "openingPositions" as const, label: "Opening Positions", Icon: Building2, color: "text-gray-500 dark:text-gray-400" },
  { key: "averageSalary" as const, label: "Average Salary", Icon: DollarSign, color: "text-emerald-500" },
  { key: "growthRate" as const, label: "Growth Rate", Icon: TrendingUp, color: "text-primary" },
];

export default function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-5xl mx-auto px-4 py-10">
      {iconMap.map(({ key, label, Icon, color }) => (
        <div key={key} className="flex items-center gap-4 p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800 ${color}`}>
            <Icon size={20} />
          </div>
          <div>
            <p className="text-xs text-gray-400 dark:text-gray-500">{label}</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {stats[key]}
            </p>
          </div>
        </div> 
      ))}
    </div>
  );
}
