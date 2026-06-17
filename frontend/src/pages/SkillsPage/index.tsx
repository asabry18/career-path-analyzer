import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import PrimaryButton from "../../components/PrimaryButton";
import SkillSearch from "../../components/SkillSearch";
import SkillSlider from "../../components/SkillSlider";
import { useAnalysis } from "../../context/useAnalysis";
import { fetchSkills } from "../../api/client";
import type { Skill, SkillLevel, CatalogSkill } from "../../types";

export default function SkillsPage() {
  const navigate = useNavigate();
  const { skills, setSkills } = useAnalysis();

  const [localSkills, setLocalSkills] = useState<Skill[]>(skills);
  const [catalogSkills, setCatalogSkills] = useState<CatalogSkill[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [formHint, setFormHint] = useState<string | null>(null);

  useEffect(() => {
    fetchSkills()
      .then(setCatalogSkills)
      .catch(() => setCatalogSkills([]))
      .finally(() => setCatalogLoading(false));
  }, []);

  const activeNames = new Set(localSkills.map((s) => s.name.toLowerCase()));
  const catalogSet = new Set(catalogSkills.map((s) => s.name.toLowerCase()));
  const availableSuggestions = catalogSkills
    .map((s) => s.name)
    .filter((name) => !activeNames.has(name.toLowerCase()));
  const canProceed =
    localSkills.length > 0 && localSkills.every((s) => Boolean(s.level));

  function updateLevel(name: string, level: SkillLevel) {
    setFormHint(null);
    setLocalSkills((prev) =>
      prev.map((s) => (s.name === name ? { ...s, level } : s))
    );
  }

  function removeSkill(name: string) {
    setFormHint(null);
    setLocalSkills((prev) => prev.filter((s) => s.name !== name));
  }

  function addSkill(name: string) {
    const trimmed = name.trim();
    const normalized = trimmed.toLowerCase();
    if (!trimmed || activeNames.has(normalized)) return;
    if (!catalogSet.has(normalized)) {
      setFormHint("Choose a skill from the catalog list.");
      return;
    }
    setFormHint(null);
    setLocalSkills((prev) => [...prev, { name: trimmed, level: "Beginner" }]);
  }

  function handleNext() {
    if (!canProceed) {
      setFormHint("Add at least one skill and choose a level for each.");
      return;
    }
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
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
          Select skills from the catalog list and choose a level for each one.
        </p>

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
        disabled={!canProceed}
      />

      {formHint && (
        <p className="text-center text-sm text-red-500 dark:text-red-400 mt-3">
          {formHint}
        </p>
      )}
    </PageLayout>
  );
}
