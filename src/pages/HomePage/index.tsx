import ThemeToggle from "../../components/ThemeToggle";
import Hero from "../../components/Hero";
import StatsCards from "../../components/StatsCards";
import CareerChart from "../../components/CareerChart";
import { useTheme } from "../../hooks/useTheme";
import { careerData } from "../../data/careers";

export default function HomePage() {
  const { isDark, toggle } = useTheme();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <ThemeToggle isDark={isDark} onToggle={toggle} />
      <main>
        <Hero />
        <StatsCards stats={careerData.stats} />
        <CareerChart careers={careerData.topCareers} />
      </main>
    </div>
  );
}
