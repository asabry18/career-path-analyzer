import { ArrowRight, Loader2 } from "lucide-react";

interface PrimaryButtonProps {
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  loading?: boolean;
}

export default function PrimaryButton({ label, onClick, disabled, loading }: PrimaryButtonProps) {
  return (
    <div className="flex justify-end mt-8">
      <button
        onClick={onClick}
        disabled={disabled || loading}
        className="flex items-center gap-2 px-8 py-3.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-base hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {loading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            {label}
            <ArrowRight size={18} />
          </>
        )}
      </button>
    </div>
  );
}
