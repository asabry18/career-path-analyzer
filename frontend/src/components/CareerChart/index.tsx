import { useState } from "react";
import type { Career } from "../../types";

interface CareerChartProps {
  careers: Career[];
}

const MAX_SALARY = 8000;
const Y_LABELS = [0, 2000, 4000, 6000, 8000];

export default function CareerChart({ careers }: CareerChartProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  return (
    <section className="max-w-5xl mx-auto px-4 py-10">
      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 sm:p-8">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          Top 5 In-Demand Tech Careers
        </h2>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 mb-8">
          Average salary in thousands (EGP)
        </p>

        <div className="flex items-end gap-2 sm:gap-4">
          <div className="flex flex-col justify-between h-56 sm:h-64 pr-2 pb-8">
            {[...Y_LABELS].reverse().map((val) => (
              <span key={val} className="text-xs text-gray-400 dark:text-gray-500 leading-none">
                {val}
              </span>
            ))}
          </div>

          <div className="flex-1 flex items-end justify-around gap-2 sm:gap-6 h-56 sm:h-64">
            {careers.map((career) => {
              const heightPct = (career.salary / MAX_SALARY) * 100;
              const isHovered = hoveredId === career.id;

              return (
                <div key={career.id} className="flex flex-col items-center flex-1 h-full justify-end relative" onMouseEnter={() => setHoveredId(career.id)} onMouseLeave={() => setHoveredId(null)}>
                  {isHovered && (
                    <div className="absolute bottom-full mb-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap z-10 bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 shadow-lg">
                      <p>{career.title}</p>
                      <p>salary: {career.salary.toLocaleString()}</p>
                    </div>
                  )}

                  <div className={`w-full max-w-16 rounded-t-md transition-all duration-300 cursor-pointer ${isHovered ? "bg-gray-900 dark:bg-white" : "bg-gray-800 dark:bg-gray-100"}`} style={{ height: `${heightPct}%` }} />
                    <span className="mt-2 text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 text-center leading-tight">
                      {career.title}
                    </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
