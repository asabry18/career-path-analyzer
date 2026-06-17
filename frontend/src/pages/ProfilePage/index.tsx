import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageLayout from "../../components/PageLayout";
import { useAuth } from "../../context/useAuth";
import { useAnalysis } from "../../context/useAnalysis";

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { skills, priorities, result, runAnalysis, loading, error } = useAnalysis();
  const [localError, setLocalError] = useState<string | null>(null);

  const fullName = user
    ? `${user.first_name} ${user.last_name}`.trim()
    : "Profile";

  const initials = useMemo(() => {
    if (!user) return "U";
    const first = user.first_name?.trim().charAt(0) || "";
    const last = user.last_name?.trim().charAt(0) || "";
    return `${first}${last}`.toUpperCase() || "U";
  }, [user]);

  const topResult = result?.ranked_jobs?.[0];
  const skillsPreview = skills.slice(0, 4);

  async function handleRetake() {
    setLocalError(null);
    if (skills.length === 0) {
      setLocalError("Add at least one skill before running the analysis.");
      return;
    }
    const ok = await runAnalysis();
    if (ok) {
      navigate("/recommendations");
    }
  }

  return (
    <PageLayout>
      <div className="space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
              Your Profile
            </h1>
            <p className="text-gray-500 dark:text-gray-400 mt-2">
              Summary of your account, skills, priorities, and latest results.
            </p>
          </div>
          <button
            onClick={handleRetake}
            disabled={loading}
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-full
              bg-gray-900 dark:bg-white text-white dark:text-gray-900
              font-medium text-sm hover:bg-gray-800 dark:hover:bg-gray-100
              transition-colors disabled:opacity-50"
          >
            {loading ? "Running analysis..." : "Retake Test"}
          </button>
        </div>

        {(localError || error) && (
          <div className="rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-5 py-3">
            <p className="text-sm text-red-700 dark:text-red-300">
              {localError || error}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr,1fr] gap-6">
          <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
            <div className="flex items-center gap-4">
              <div className="h-14 w-14 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900
                flex items-center justify-center text-lg font-bold">
                {initials}
              </div>
              <div>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {fullName || "User"}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {user?.email || ""}
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <button
                onClick={() => navigate("/skills")}
                className="text-left rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60 p-4 hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
              >
                <p className="text-xs text-gray-500 dark:text-gray-400">Skills</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {skills.length}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Add or remove skills
                </p>
              </button>

              <button
                onClick={() => navigate("/priorities")}
                className="text-left rounded-xl border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/60 p-4 hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
              >
                <p className="text-xs text-gray-500 dark:text-gray-400">Priorities</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                  {priorities.length}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Reorder to change weights
                </p>
              </button>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Latest Result
              </h2>
              <button
                onClick={() => navigate("/recommendations")}
                className="text-sm font-semibold text-primary hover:underline"
              >
                View results
              </button>
            </div>

            {topResult ? (
              <div className="mt-4 space-y-2">
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  {topResult.title}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Fit score: {(topResult.topsis_score * 100).toFixed(1)}% ·
                  Match: {(topResult.skill_match_score * 100).toFixed(1)}%
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Jobs evaluated: {result?.meta.jobs_evaluated || 0} · Passed threshold: {result?.meta.jobs_after_threshold || 0}
                </p>
              </div>
            ) : (
              <div className="mt-4">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  No analysis results yet. Run the test to see recommendations.
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <button
            onClick={() => navigate("/skills")}
            className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 text-left hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Skills snapshot
              </h3>
              <span className="text-sm text-primary">Edit skills</span>
            </div>
            {skillsPreview.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {skillsPreview.map((skill) => (
                  <span
                    key={skill.name}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                  >
                    {skill.name} · {skill.level}
                  </span>
                ))}
                {skills.length > skillsPreview.length && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    +{skills.length - skillsPreview.length} more
                  </span>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
                No skills selected yet. Add skills to start your analysis.
              </p>
            )}
          </button>

          <button
            onClick={() => navigate("/priorities")}
            className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6 text-left hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Priority order
              </h3>
              <span className="text-sm text-primary">Edit priorities</span>
            </div>
            <ol className="mt-4 space-y-2">
              {priorities.map((p, idx) => (
                <li key={p.id} className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>{idx + 1}. {p.label}</span>
                  <span className="text-xs text-gray-400 dark:text-gray-500">{p.description}</span>
                </li>
              ))}
            </ol>
          </button>
        </div>
      </div>
    </PageLayout>
  );
}
