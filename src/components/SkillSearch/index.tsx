import { useState } from "react";
import { Search } from "lucide-react";

interface SkillSearchProps {
  suggestions: string[];
  onSelect: (name: string) => void;
}

export default function SkillSearch({ suggestions, onSelect }: SkillSearchProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);

  const filtered = suggestions.filter((s) =>
    s.toLowerCase().includes(query.toLowerCase())
  );

  function handleSelect(name: string) {
    onSelect(name);
    setQuery("");
    setOpen(false);
  }

  return (
    <div className="relative mb-4">
      <Search
        size={16}
        className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400"
      />
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder="Search skills to add..."
        className="w-full pl-10 pr-4 py-2.5 rounded-full bg-gray-100 dark:bg-gray-800
          text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500
          border border-gray-200 dark:border-gray-700 outline-none
          focus:ring-2 focus:ring-primary/40 transition text-sm"
      />

      {open && query && filtered.length > 0 && (
        <div className="absolute z-20 left-0 right-0 mt-2 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-lg max-h-48 overflow-y-auto">
          {filtered.map((s) => (
            <button
              key={s}
              onMouseDown={() => handleSelect(s)}
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
  );
}
