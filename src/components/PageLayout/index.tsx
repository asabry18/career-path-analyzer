import ThemeToggle from "../ThemeToggle";
import { useTheme } from "../../hooks/useTheme";

interface PageLayoutProps {
  children: React.ReactNode;
}

export default function PageLayout({ children }: PageLayoutProps) {
  const { isDark, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <ThemeToggle isDark={isDark} onToggle={toggle} />
      <div className="max-w-5xl mx-auto px-4 py-10">{children}</div>
    </div>
  );
}
