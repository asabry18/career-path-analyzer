import { ChevronUp, ChevronDown, DollarSign, TrendingUp, Eye, GraduationCap, GripVertical} from "lucide-react";
import type { Priority } from "../../types";
import "./PriorityCard.css";

const ICONS: Record<string, React.ReactNode> = {
  salary: <DollarSign size={20} />,
  demand: <TrendingUp size={20} />,
  match: <Eye size={20} />,
  learn: <GraduationCap size={20} />,
};

const PRIORITY_LABELS = [
  "Highest Priority",
  "High Priority",
  "Medium Priority",
  "Low Priority",
];

const POSITION_WEIGHTS = [10, 7, 4, 1];

interface PriorityCardProps {
  priority: Priority;
  index: number;
  total: number;
  isDragging: boolean;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDragStart: () => void;
  onDragOver: () => void;
  onDragEnd: () => void;
}

export default function PriorityCard({
  priority,
  index,
  total,
  isDragging,
  onMoveUp,
  onMoveDown,
  onDragStart,
  onDragOver,
  onDragEnd,
}: PriorityCardProps) {
  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onDragOver={(e) => {
        e.preventDefault();
        onDragOver();
      }}
      className={`group rounded-2xl border bg-white dark:bg-gray-900
        px-5 py-4 flex items-center gap-4 transition-all select-none
        ${isDragging
          ? "opacity-50 scale-[0.98] border-primary/40"
          : "border-gray-200 dark:border-gray-700"
        }`}
    >
      <span className="text-gray-400 dark:text-gray-500 cursor-grab active:cursor-grabbing">
        <GripVertical size={20} />
      </span>

      <span className="flex-shrink-0 w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-800
        flex items-center justify-center text-sm font-bold text-gray-900 dark:text-white">
        {index + 1}
      </span>

      <span className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-900 dark:bg-white
        flex items-center justify-center text-white dark:text-gray-900">
        {ICONS[priority.icon]}
      </span>

      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-gray-900 dark:text-white leading-tight">
          {priority.label}
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
          {priority.description}
        </p>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="text-xs font-medium text-primary">
            {PRIORITY_LABELS[index]}
          </span>
          <span className="priority-card__weight">
            Weight: {POSITION_WEIGHTS[index]}/10
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-0.5">
        <button
          onClick={onMoveUp}
          disabled={index === 0}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800
            text-gray-600 dark:text-gray-300 disabled:opacity-30
            transition-colors cursor-pointer disabled:cursor-default"
        >
          <ChevronUp size={18} />
        </button>
        <button
          onClick={onMoveDown}
          disabled={index === total - 1}
          className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800
            text-gray-600 dark:text-gray-300 disabled:opacity-30
            transition-colors cursor-pointer disabled:cursor-default"
        >
          <ChevronDown size={18} />
        </button>
      </div>
    </div>
  );
}
