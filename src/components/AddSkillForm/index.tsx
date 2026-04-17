import { Plus } from "lucide-react";

interface AddSkillFormProps {
  value: string;
  onChange: (value: string) => void;
  onAdd: (name: string) => void;
}

export default function AddSkillForm({ value, onChange, onAdd }: AddSkillFormProps) {
  return (
    <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 mb-6">
      <h2 className="font-semibold text-gray-900 dark:text-white mb-4">
        Add Custom Skill
      </h2>
      <div className="flex gap-3">
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)} onKeyDown={(e) => e.key === "Enter" && onAdd(value)} placeholder="Enter a skill name..." className="flex-1 px-4 py-2.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 border border-gray-200 dark:border-gray-700 outline-none focus:ring-2 focus:ring-primary/40 transition"/>
        <button onClick={() => onAdd(value)} className="flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer">
          <Plus size={16} />
          Add
        </button>
      </div>
    </div>
  );
}
