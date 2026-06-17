import { Moon, Sun } from "lucide-react";

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
  className?: string;
}

export default function ThemeToggle({ isDark, onToggle, className }: ThemeToggleProps) {
  return (
    <button
      onClick={onToggle}
      aria-label="Toggle theme"
      className={`rounded-full p-2.5
        bg-gray-100 dark:bg-gray-800
        text-gray-700 dark:text-gray-200
        hover:bg-gray-200 dark:hover:bg-gray-700
        transition-colors cursor-pointer ${className ?? ""}`}
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}
