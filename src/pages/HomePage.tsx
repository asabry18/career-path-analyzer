import ThemeToggle from "../components/ThemeToggle";
import Hero from "../components/Hero";
import StatsCards from "../components/StatsCards";
import CareerChart from "../components/CareerChart";
import { useTheme } from "../hooks/useTheme";
import careerData from "../data/careers.json";
import type { CareerData } from "../types";

const data = careerData as CareerData;

export default function HomePage() {
  const { isDark, toggle } = useTheme();

  return (
    <div className="container bg-white dark:bg-gray-950 transition-colors">
      <ThemeToggle isDark={isDark} onToggle={toggle} />
      <main className="mx-auto">
        <Hero />
        <StatsCards stats={data.stats} />
        <CareerChart careers={data.topCareers} />
      </main>
    </div>
  );
}
