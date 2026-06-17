import { useMemo, useState } from "react";

interface ChartItem {
  id: number;
  label: string;
  value: number;
}

interface CareerChartProps {
  title: string;
  subtitle: string;
  items: ChartItem[];
  valueSuffix?: string;
}

export default function CareerChart({ title, subtitle, items, valueSuffix = "" }: CareerChartProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const maxValue = useMemo(() => {
    if (!items.length) return 1;
    return Math.max(...items.map((item) => item.value), 1);
  }, [items]);

  const ticks = useMemo(() => {
    const steps = 4;
    return Array.from({ length: steps + 1 }, (_, i) => (maxValue / steps) * i);
  }, [maxValue]);

  return (
    <section className="max-w-5xl mx-auto px-4 py-10">
      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 sm:p-8">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          {title}
        </h2>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1 mb-8">
          {subtitle}
        </p>

        <div className="flex items-end gap-2 sm:gap-4">
          <div className="flex flex-col justify-between h-56 sm:h-64 pr-2 pb-8">
            {[...ticks].reverse().map((val) => (
              <span key={val} className="text-xs text-gray-400 dark:text-gray-500 leading-none">
                {val.toFixed(0)}{valueSuffix}
              </span>
            ))}
          </div>

          <div className="flex-1 flex items-end justify-around gap-2 sm:gap-6 h-56 sm:h-64">
            {items.map((item) => {
              const heightPct = (item.value / maxValue) * 100;
              const isHovered = hoveredId === item.id;

              return (
                <div key={item.id} className="flex flex-col items-center flex-1 h-full justify-end relative" onMouseEnter={() => setHoveredId(item.id)} onMouseLeave={() => setHoveredId(null)}>
                  {isHovered && (
                    <div className="absolute bottom-full mb-2 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap z-10 bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 shadow-lg">
                      <p>{item.label}</p>
                      <p>value: {item.value.toLocaleString()}{valueSuffix}</p>
                    </div>
                  )}

                  <div className={`w-full max-w-16 rounded-t-md transition-all duration-300 cursor-pointer ${isHovered ? "bg-gray-900 dark:bg-white" : "bg-gray-800 dark:bg-gray-100"}`} style={{ height: `${heightPct}%` }} />
                    <span className="mt-2 text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 text-center leading-tight">
                      {item.label}
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
