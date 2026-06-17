import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Layers } from "lucide-react";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import CareerCard from "../../components/CareerCard";
import CareerDetail from "../../components/CareerDetail";
import CourseCard from "../../components/CourseCard";
import { useAnalysis } from "../../context/useAnalysis";
import { mapResultToRecommendations } from "../../utils/mappers";
import "./RecommendationsPage.css";

export default function RecommendationsPage() {
  const navigate = useNavigate();
  const { result, loading, error } = useAnalysis();
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (loading) {
    return (
      <PageLayout>
        <BackButton to="/priorities" />
        <div className="flex flex-col items-center justify-center py-24">
          <div className="w-10 h-10 border-4 border-gray-300 dark:border-gray-600 border-t-gray-900 dark:border-t-white rounded-full animate-spin" />
          <p className="mt-4 text-gray-500 dark:text-gray-400">
            Analyzing your career path...
          </p>
        </div>
      </PageLayout>
    );
  }

  if (error || !result) {
    return (
      <PageLayout>
        <BackButton to="/priorities" />
        <div className="flex flex-col items-center justify-center py-24">
          <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {error ? "Analysis Failed" : "No Results Yet"}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 text-center max-w-md">
            {error || "Please go back and add your skills and priorities to get career recommendations."}
          </p>
          <button
            onClick={() => navigate("/skills")}
            className="px-6 py-2.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-sm hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer"
          >
            Start Over
          </button>
        </div>
      </PageLayout>
    );
  }

  const recommendations = mapResultToRecommendations(result);

  if (recommendations.length === 0) {
    return (
      <PageLayout>
        <BackButton to="/priorities" />
        <div className="flex flex-col items-center justify-center py-24">
          <p className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Matching Careers
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 text-center max-w-md">
            No jobs passed the similarity threshold. Try adding more skills or
            lowering the threshold.
          </p>
          <button
            onClick={() => navigate("/skills")}
            className="px-6 py-2.5 rounded-full bg-gray-900 dark:bg-white text-white dark:text-gray-900 font-medium text-sm hover:bg-gray-800 dark:hover:bg-gray-100 transition-colors cursor-pointer"
          >
            Update Skills
          </button>
        </div>
      </PageLayout>
    );
  }

  const selected = recommendations[selectedIdx] ?? recommendations[0];

  return (
    <PageLayout>
      <BackButton to="/priorities" />
      <PageHeader title="Your Career Recommendations" subtitle="" />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {recommendations.slice(0, 3).map((career, i) => (
          <CareerCard
            key={career.id}
            career={career}
            isSelected={i === selectedIdx}
            onClick={() => setSelectedIdx(i)}
          />
        ))}
      </div>

      <CareerDetail career={selected} />

      {selected.skillGaps.length > 0 && (
        <div className="mt-8 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Missing Mandatory Skills
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-6">
            Skills you need to learn for this career
          </p>

          <div className="space-y-6">
            {selected.skillGaps.map((gap) => (
              <div key={gap.name}>
                <div className="flex items-center justify-between mb-1">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {gap.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Current: {gap.current} &rarr; Target: {gap.target}
                    </p>
                  </div>
                  <div className="w-40">
                    <div className="skill-gap__progress-track">
                      <div
                        className="skill-gap__progress-fill"
                        style={{ width: `${gap.progress}%` }}
                      />
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-3 mt-3">
                  {gap.courses.map((course) => (
                    <CourseCard key={course.title} course={course} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selected.frameworkChoices.length > 0 && (
        <div className="mt-8 rounded-2xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20 p-6">
          <div className="flex items-center gap-2 mb-1">
            <Layers size={20} className="text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Framework Choices
            </h2>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            This job requires one of the following frameworks — you only need to learn <strong>one</strong> from each group
          </p>

          <div className="space-y-5">
            {selected.frameworkChoices.map((fc, i) => (
              <div key={i}>
                <p className="text-xs font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide mb-2">
                  {fc.slotLabel} — pick one
                </p>
                <div className="flex flex-wrap gap-2">
                  {fc.alternatives.map((alt) => (
                    <span
                      key={alt}
                      className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium border border-blue-300 dark:border-blue-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
                    >
                      {alt}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {result.learning_plan.selected_courses.length > 0 && (
        <div className="mt-8 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Recommended Learning Plan
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-6">
            The minimum set of courses (via Set Cover algorithm) to cover all your
            missing skills across every recommended career
          </p>
          <div className="flex flex-col gap-4">
            {result.learning_plan.selected_courses.map((course) => (
              <div
                key={course.course_id}
                className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden"
              >
                <CourseCard
                  course={{
                    title: course.title,
                    platform: course.provider,
                    duration: `Covers ${course.skills.length} skill${course.skills.length !== 1 ? "s" : ""}`,
                    url: course.url,
                  }}
                />
                {course.skills.length > 0 && (
                  <div className="px-5 pb-4 flex flex-wrap gap-2">
                    {course.skills.map((sk) => (
                      <span
                        key={sk.skill_id}
                        className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300"
                      >
                        {sk.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {result.learning_plan.uncovered_skills.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                Skills not covered by available courses:
              </p>
              <div className="flex flex-wrap gap-2">
                {result.learning_plan.uncovered_skills.map((sk) => (
                  <span
                    key={sk.skill_id}
                    className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300"
                  >
                    ✗ {sk.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {result.ranked_jobs.length > 3 && (
        <div className="mt-8 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            All Ranked Careers
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="py-2 px-3 text-left text-gray-500 dark:text-gray-400 font-medium">#</th>
                  <th className="py-2 px-3 text-left text-gray-500 dark:text-gray-400 font-medium">Career</th>
                  <th className="py-2 px-3 text-right text-gray-500 dark:text-gray-400 font-medium">Skill Match</th>
                  <th className="py-2 px-3 text-right text-gray-500 dark:text-gray-400 font-medium">Fit Score</th>
                  <th className="py-2 px-3 text-right text-gray-500 dark:text-gray-400 font-medium">Salary</th>
                  <th className="py-2 px-3 text-right text-gray-500 dark:text-gray-400 font-medium">Demand</th>
                  <th className="py-2 px-3 text-right text-gray-500 dark:text-gray-400 font-medium">Effort</th>
                </tr>
              </thead>
              <tbody>
                {result.ranked_jobs.map((job) => (
                  <tr
                    key={job.job_id}
                    className="border-b border-gray-100 dark:border-gray-800"
                  >
                    <td className="py-2.5 px-3 font-medium text-gray-900 dark:text-white">{job.rank}</td>
                    <td className="py-2.5 px-3 text-gray-900 dark:text-white">{job.title}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">{(job.skill_match_score * 100).toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">{(job.topsis_score * 100).toFixed(1)}%</td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">{job.avg_salary.toLocaleString()}K</td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">{job.demand_score}</td>
                    <td className="py-2.5 px-3 text-right text-gray-600 dark:text-gray-300">{job.learning_effort}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PageLayout>
  );
}
