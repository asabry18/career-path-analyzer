import { Trophy, TrendingUp } from "lucide-react";
import type { CareerRecommendation } from "../../types";
import "./CareerCard.css";

const RANK_STYLES: Record<number, { label: string; color: string }> = {
  1: { label: "1st", color: "career-card__rank--gold" },
  2: { label: "2nd", color: "career-card__rank--silver" },
  3: { label: "3rd", color: "career-card__rank--bronze" },
};

interface CareerCardProps {
  career: CareerRecommendation;
  isSelected: boolean;
  onClick: () => void;
}

export default function CareerCard({ career, isSelected, onClick }: CareerCardProps) {
  const rank = RANK_STYLES[career.rank];

  return (
    <button
      onClick={onClick}
      className={`w-full text-left rounded-2xl border p-5 transition-all cursor-pointer
        bg-white dark:bg-gray-900
        ${isSelected
          ? "border-gray-900 dark:border-white ring-1 ring-gray-900 dark:ring-white"
          : "border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500"
        }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`flex items-center gap-1.5 text-sm font-bold ${rank.color}`}>
          <Trophy size={16} />
          {rank.label}
        </div>
        <span className="text-lg font-bold text-gray-900 dark:text-white">
          {career.matchScore}%
        </span>
      </div>

      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
        {career.title}
      </h3>

      <div className="space-y-1 text-sm text-gray-500 dark:text-gray-400">
        <p>
          Avg Salary:{" "}
          <span className="font-medium text-gray-900 dark:text-white">
            {career.avgSalary}
          </span>
        </p>
        <p className="flex items-center gap-1">
          Growth:{" "}
          <TrendingUp size={14} />
          <span className="font-medium text-gray-900 dark:text-white">
            {career.growth}
          </span>
        </p>
      </div>
    </button>
  );
}
