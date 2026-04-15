import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";

export default function Hero() {
  const navigate = useNavigate();

  return (
    <section className="flex flex-col items-center text-center pt-20 pb-10 px-4">
      <div
        className="flex items-center gap-2 px-4 py-2 rounded-full mb-8 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
        <Sparkles size={16} className="text-primary" />
        <span>AI-Powered Career Guidance</span>
      </div>

      <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-gray-900 dark:text-white">
        Find Your Perfect{" "}
        <span className="text-primary">Career Path</span>
      </h1>

      <p className="mt-6 text-lg text-gray-500 dark:text-gray-400 max-w-2xl">
        Discover high-demand careers matched to your skills. Get personalized recommendations and bridge your skill gaps.
      </p>

      <button
        onClick={() => navigate("/skills")}
        className="mt-10 flex items-center gap-2 px-8 py-3.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-base hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer"
      >
        Start Your Journey
        <ArrowRight size={18} />
      </button>
    </section>
  );
}
