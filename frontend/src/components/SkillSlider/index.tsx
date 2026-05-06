import type { SkillLevel } from "../../types";

interface SkillSliderProps {
  name: string;
  level: SkillLevel;
  onChange: (level: SkillLevel) => void;
}

const LEVELS: SkillLevel[] = ["Beginner", "Intermediate", "Advanced"];

export default function SkillSlider({ name, level, onChange }: SkillSliderProps) {
  const index = LEVELS.indexOf(level);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    onChange(LEVELS[Number(e.target.value)]);
  }

  return (
    <div className="py-4">
      <div className="flex items-center justify-between mb-2">
        <span className="font-semibold text-gray-900 dark:text-white">{name}</span>
        <span className="text-sm font-medium text-gray-900 dark:text-white">{level}</span>
      </div>

      <input
        type="range"
        min={0}
        max={2}
        step={1}
        value={index}
        onChange={handleChange}
        className="w-full h-2 rounded-full appearance-none cursor-pointer bg-gray-300 dark:bg-gray-600 accent-gray-900 dark:accent-white"
      />

      <div className="flex justify-between mt-1.5">
        {LEVELS.map((l) => (
          <span
            key={l}
            className={`text-xs ${l === level ? "text-gray-700 dark:text-gray-200" : "text-gray-400 dark:text-gray-500"}`}
          >
            {l}
          </span>
        ))}
      </div>
    </div>
  );
}
