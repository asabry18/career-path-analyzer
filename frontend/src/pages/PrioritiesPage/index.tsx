import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import PrimaryButton from "../../components/PrimaryButton";
import PriorityCard from "../../components/PriorityCard";
import { useAnalysis } from "../../context/AnalysisContext";
import "./PrioritiesPage.css";

export default function PrioritiesPage() {
  const navigate = useNavigate();
  const { priorities, setPriorities, skills, runAnalysis, loading, error } =
    useAnalysis();

  const dragItem = useRef<number | null>(null);
  const dragOverItem = useRef<number | null>(null);
  const [draggingIdx, setDraggingIdx] = useState<number | null>(null);

  function swap(a: number, b: number) {
    setPriorities(
      priorities.map((p, i) =>
        i === a ? priorities[b] : i === b ? priorities[a] : p
      )
    );
  }

  function handleDragStart(index: number) {
    dragItem.current = index;
    setDraggingIdx(index);
  }

  function handleDragOver(index: number) {
    dragOverItem.current = index;
  }

  function handleDragEnd() {
    const from = dragItem.current;
    const to = dragOverItem.current;
    if (from !== null && to !== null && from !== to) {
      const next = [...priorities];
      const [removed] = next.splice(from, 1);
      next.splice(to, 0, removed);
      setPriorities(next);
    }
    dragItem.current = null;
    dragOverItem.current = null;
    setDraggingIdx(null);
  }

  async function handleAnalyze() {
    await runAnalysis();
    navigate("/recommendations");
  }

  return (
    <PageLayout>
      <BackButton to="/skills" />
      <PageHeader
        title="Set Your Priorities"
        subtitle="Rank what matters most to you in your future career"
      />

      <div className="rounded-2xl bg-gray-100 dark:bg-gray-800/60 px-6 py-4 mb-6">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          <span className="font-semibold text-gray-900 dark:text-white">
            Drag to reorder
          </span>{" "}
          or use the arrow buttons to set your priorities from most to least
          important
          <span className="priorities-hint">
            Each priority carries a weight based on its rank — higher rank means
            more influence on your recommendations
          </span>
        </p>
      </div>

      <div className="flex flex-col gap-3">
        {priorities.map((p, i) => (
          <PriorityCard
            key={p.id}
            priority={p}
            index={i}
            total={priorities.length}
            isDragging={draggingIdx === i}
            onMoveUp={() => i > 0 && swap(i, i - 1)}
            onMoveDown={() => i < priorities.length - 1 && swap(i, i + 1)}
            onDragStart={() => handleDragStart(i)}
            onDragOver={() => handleDragOver(i)}
            onDragEnd={handleDragEnd}
          />
        ))}
      </div>

      {error && (
        <div className="mt-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-5 py-3">
          <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
        </div>
      )}

      <PrimaryButton
        label="View Recommendations"
        onClick={handleAnalyze}
        disabled={skills.length === 0}
        loading={loading}
      />

      {skills.length === 0 && (
        <p className="text-center text-sm text-gray-400 dark:text-gray-500 mt-2">
          Go back and add at least one skill first.
        </p>
      )}
    </PageLayout>
  );
}
