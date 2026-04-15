import { Moon, Sun } from "lucide-react";

interface ThemeToggleProps {
  isDark: boolean;
  onToggle: () => void;
}

export default function ThemeToggle({ isDark, onToggle }: ThemeToggleProps) {
  return (
    <button
      onClick={onToggle}
      aria-label="Toggle theme"
      className="fixed top-6 right-6 z-50 rounded-full p-2.5 
        bg-gray-100 dark:bg-gray-800 
        text-gray-700 dark:text-gray-200
        hover:bg-gray-200 dark:hover:bg-gray-700
        transition-colors cursor-pointer"
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  );
}
