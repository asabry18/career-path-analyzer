import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Plus, Search } from "lucide-react";
import ThemeToggle from "../components/ThemeToggle";
import SkillSlider from "../components/SkillSlider";
import { useTheme } from "../hooks/useTheme";
import type { Skill, SkillLevel } from "../types";

const DEFAULT_SKILLS: Skill[] = [
  { name: "JavaScript", level: "Beginner" },
  { name: "Python", level: "Beginner" },
  { name: "Machine Learning", level: "Beginner" },
  { name: "Data Analysis", level: "Beginner" },
  { name: "TensorFlow", level: "Beginner" },
  { name: "Statistics", level: "Beginner" },
];

const AVAILABLE_SKILLS = [
  "JavaScript", "Python", "Machine Learning", "Data Analysis",
  "TensorFlow", "Statistics", "React", "Node.js", "TypeScript",
  "SQL", "Docker", "AWS", "Git", "Java", "C++", "Rust",
  "Kubernetes", "GraphQL", "MongoDB", "PostgreSQL", "Redis",
  "Flutter", "Swift", "Kotlin", "Go", "Ruby", "PHP",
  "Cybersecurity", "DevOps", "Cloud Architecture",
];

export default function SkillsPage() {
  const { isDark, toggle } = useTheme();
  const navigate = useNavigate();
  const [skills, setSkills] = useState<Skill[]>(DEFAULT_SKILLS);
  const [customSkill, setCustomSkill] = useState("");
  const [search, setSearch] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(false);

  const activeNames = new Set(skills.map((s) => s.name));
  const suggestions = AVAILABLE_SKILLS.filter(
    (s) => !activeNames.has(s) && s.toLowerCase().includes(search.toLowerCase())
  );

  function updateLevel(name: string, level: SkillLevel) {
    setSkills((prev) =>
      prev.map((s) => (s.name === name ? { ...s, level } : s))
    );
  }

  function addSkill(name: string) {
    const trimmed = name.trim();
    if (!trimmed || activeNames.has(trimmed)) return;
    setSkills((prev) => [...prev, { name: trimmed, level: "Beginner" }]);
    setCustomSkill("");
    setSearch("");
    setShowSuggestions(false);
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <ThemeToggle isDark={isDark} onToggle={toggle} />

      <div className="max-w-5xl mx-auto px-4 py-10">
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-1.5 text-sm text-primary hover:underline mb-4 cursor-pointer"
        >
          <ArrowLeft size={16} />
          Back
        </button>

        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
          Rate Your Skills
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2 mb-8">
          Select your proficiency level for each skill
        </p>

        {/* Add Custom Skill */}
        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 mb-6">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">
            Add Custom Skill
          </h2>
          <div className="flex gap-3">
            <input
              type="text"
              value={customSkill}
              onChange={(e) => setCustomSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addSkill(customSkill)}
              placeholder="Enter a skill name..."
              className="flex-1 px-4 py-2.5 rounded-full bg-gray-100 dark:bg-gray-800
                text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500
                border border-gray-200 dark:border-gray-700 outline-none
                focus:ring-2 focus:ring-primary/40 transition"
            />
            <button
              onClick={() => addSkill(customSkill)}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-full
                bg-gray-900 dark:bg-white text-white dark:text-gray-900
                font-medium hover:bg-gray-800 dark:hover:bg-gray-100
                transition-colors cursor-pointer"
            >
              <Plus size={16} />
              Add
            </button>
          </div>
        </div>

        {/* Your Skills */}
        <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
          <div className="flex items-center justify-between mb-2">
            <h2 className="font-semibold text-gray-900 dark:text-white">
              Your Skills
            </h2>
          </div>

          {/* Search */}
          <div className="relative mb-4">
            <Search
              size={16}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setShowSuggestions(true);
              }}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
              placeholder="Search skills to add..."
              className="w-full pl-10 pr-4 py-2.5 rounded-full bg-gray-100 dark:bg-gray-800
                text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500
                border border-gray-200 dark:border-gray-700 outline-none
                focus:ring-2 focus:ring-primary/40 transition text-sm"
            />

            {showSuggestions && search && suggestions.length > 0 && (
              <div className="absolute z-20 left-0 right-0 mt-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg max-h-48 overflow-y-auto">
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onMouseDown={() => addSkill(s)}
                    className="w-full text-left px-4 py-2.5 text-sm text-gray-700 dark:text-gray-300
                      hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer
                      first:rounded-t-xl last:rounded-b-xl"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Skill list */}
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {skills.map((skill) => (
              <SkillSlider
                key={skill.name}
                name={skill.name}
                level={skill.level}
                onChange={(level) => updateLevel(skill.name, level)}
              />
            ))}
          </div>
        </div>

        {/* View Recommendations */}
        <div className="flex justify-end mt-8">
          <button
            className="flex items-center gap-2 px-8 py-3.5 rounded-full
              bg-gray-900 dark:bg-white text-white dark:text-gray-900
              font-medium text-base hover:bg-gray-800 dark:hover:bg-gray-100
              transition-colors cursor-pointer"
          >
            View Recommendations
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
