import type { CareerRecommendation } from "../../types";

interface CareerDetailProps {
  career: CareerRecommendation;
}

export default function CareerDetail({ career }: CareerDetailProps) {
  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
      <h2 className="text-xl font-bold text-gray-900 dark:text-white">
        {career.title}
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
        {career.description}
      </p>

      <div className="flex gap-4 mt-5">
        <div className="flex-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Avg Salary</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">
            {career.avgSalary}
          </p>
        </div>
        <div className="flex-1 rounded-xl bg-gray-100 dark:bg-gray-800 p-4">
          <p className="text-xs text-gray-500 dark:text-gray-400">Growth</p>
          <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">
            {career.growth}
          </p>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
          Match Score
        </p>
        <div className="w-full h-2 rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-2 rounded-full bg-primary transition-all duration-500"
            style={{ width: `${career.matchScore}%` }}
          />
        </div>
        <p className="text-right text-sm font-bold text-gray-900 dark:text-white mt-1">
          {career.matchScore}%
        </p>
      </div>
    </div>
  );
}
