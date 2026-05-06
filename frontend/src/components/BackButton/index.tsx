import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

interface BackButtonProps {
  to: string;
}

export default function BackButton({ to }: BackButtonProps) {
  const navigate = useNavigate();

  return (
    <button onClick={() => navigate(to)} className="flex items-center gap-1.5 text-sm text-primary hover:underline mb-4 cursor-pointer">
      <ArrowLeft size={16} />
      Back
    </button>
  );
}
