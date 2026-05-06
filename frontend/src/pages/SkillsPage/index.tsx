import { useState } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import PrimaryButton from "../../components/PrimaryButton";
import AddSkillForm from "../../components/AddSkillForm";
import SkillSearch from "../../components/SkillSearch";
import SkillSlider from "../../components/SkillSlider";
import { DEFAULT_SKILLS, AVAILABLE_SKILLS } from "../../data/skills";
import type { Skill, SkillLevel } from "../../types";

export default function SkillsPage() {
  const navigate = useNavigate();
  const [skills, setSkills] = useState<Skill[]>(DEFAULT_SKILLS);
  const [customSkill, setCustomSkill] = useState("");

  const activeNames = new Set(skills.map((s) => s.name));
  const availableSuggestions = AVAILABLE_SKILLS.filter((s) => !activeNames.has(s));

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
  }

  return (
    <PageLayout>
      <BackButton to="/" />
      <PageHeader title="Rate Your Skills" subtitle="Select your proficiency level for each skill" />

      <AddSkillForm value={customSkill} onChange={setCustomSkill} onAdd={addSkill} />

      <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-2">
          Your Skills
        </h2>

        <SkillSearch suggestions={availableSuggestions} onSelect={addSkill} />

        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {skills.map((skill) => (
            <SkillSlider key={skill.name} name={skill.name} level={skill.level} onChange={(level) => updateLevel(skill.name, level)}/>
          ))}
        </div>
      </div>

      <PrimaryButton label="Set Priorities" onClick={() => navigate("/priorities")} />
    </PageLayout>
  );
}
