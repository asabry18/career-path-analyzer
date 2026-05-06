import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import PrimaryButton from "../../components/PrimaryButton";
import PriorityCard from "../../components/PriorityCard";
import { DEFAULT_PRIORITIES } from "../../data/priorities";
import type { Priority } from "../../types";
import "./PrioritiesPage.css";

export default function PrioritiesPage() {
  const navigate = useNavigate();
  const [priorities, setPriorities] = useState<Priority[]>(DEFAULT_PRIORITIES);
  const dragItem = useRef<number | null>(null);
  const dragOverItem = useRef<number | null>(null);
  const [draggingIdx, setDraggingIdx] = useState<number | null>(null);

  function swap(a: number, b: number) {
    setPriorities((prev) => {
      const next = [...prev];
      [next[a], next[b]] = [next[b], next[a]];
      return next;
    });
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
      setPriorities((prev) => {
        const next = [...prev];
        const [removed] = next.splice(from, 1);
        next.splice(to, 0, removed);
        return next;
      });
    }
    dragItem.current = null;
    dragOverItem.current = null;
    setDraggingIdx(null);
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

      <PrimaryButton label="View Recommendations" onClick={() => navigate("/recommendations")} />
    </PageLayout>
  );
}
