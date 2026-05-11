import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import PrimaryButton from "../../components/PrimaryButton";
import SkillSearch from "../../components/SkillSearch";
import SkillSlider from "../../components/SkillSlider";
import { useAnalysis } from "../../context/AnalysisContext";
import { fetchSkills } from "../../api/client";
import type { Skill, SkillLevel, CatalogSkill } from "../../types";

export default function SkillsPage() {
  const navigate = useNavigate();
  const { skills, setSkills } = useAnalysis();

  const [localSkills, setLocalSkills] = useState<Skill[]>(skills);
  const [catalogSkills, setCatalogSkills] = useState<CatalogSkill[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);

  useEffect(() => {
    fetchSkills()
      .then(setCatalogSkills)
      .catch(() => setCatalogSkills([]))
      .finally(() => setCatalogLoading(false));
  }, []);

  const activeNames = new Set(localSkills.map((s) => s.name.toLowerCase()));
  const availableSuggestions = catalogSkills
    .map((s) => s.name)
    .filter((name) => !activeNames.has(name.toLowerCase()));

  function updateLevel(name: string, level: SkillLevel) {
    setLocalSkills((prev) =>
      prev.map((s) => (s.name === name ? { ...s, level } : s))
    );
  }

  function removeSkill(name: string) {
    setLocalSkills((prev) => prev.filter((s) => s.name !== name));
  }

  function addSkill(name: string) {
    const trimmed = name.trim();
    if (!trimmed || activeNames.has(trimmed.toLowerCase())) return;
    setLocalSkills((prev) => [...prev, { name: trimmed, level: "Beginner" }]);
  }

  function handleNext() {
    setSkills(localSkills);
    navigate("/priorities");
  }

  return (
    <PageLayout>
      <BackButton to="/" />
      <PageHeader
        title="Rate Your Skills"
        subtitle="Select your proficiency level for each skill"
      />

      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-2">
          {catalogLoading ? "Loading skills..." : "Your Skills"}
        </h2>

        <SkillSearch suggestions={availableSuggestions} onSelect={addSkill} />

        {localSkills.length === 0 && (
          <p className="text-sm text-gray-400 dark:text-gray-500 py-8 text-center">
            Start typing above to search and add skills from the catalog.
          </p>
        )}

        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {localSkills.map((skill) => (
            <div key={skill.name} className="flex items-center gap-2">
              <div className="flex-1">
                <SkillSlider
                  name={skill.name}
                  level={skill.level}
                  onChange={(level) => updateLevel(skill.name, level)}
                />
              </div>
              <button
                onClick={() => removeSkill(skill.name)}
                className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors p-1 text-lg font-bold cursor-pointer"
                title="Remove skill"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      <PrimaryButton
        label="Set Priorities"
        onClick={handleNext}
        disabled={localSkills.length === 0}
      />
    </PageLayout>
  );
}
