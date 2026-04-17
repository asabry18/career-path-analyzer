import { ArrowRight } from "lucide-react";

interface PrimaryButtonProps {
  label: string;
  onClick?: () => void;
}

export default function PrimaryButton({ label, onClick }: PrimaryButtonProps) {
  return (
    <div className="flex justify-end mt-8">
      <button onClick={onClick} className="flex items-center gap-2 px-8 py-3.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-base hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer" >
        {label}
        <ArrowRight size={18} />
      </button>
    </div>
  );
}
