import { useState } from "react";
import PageLayout from "../../components/PageLayout";
import BackButton from "../../components/BackButton";
import PageHeader from "../../components/PageHeader";
import CareerCard from "../../components/CareerCard";
import CareerDetail from "../../components/CareerDetail";
import CourseCard from "../../components/CourseCard";
import { MOCK_RECOMMENDATIONS } from "../../data/recommendations";
import "./RecommendationsPage.css";

export default function RecommendationsPage() {
  const [selectedId, setSelectedId] = useState(MOCK_RECOMMENDATIONS[0].id);
  const selected = MOCK_RECOMMENDATIONS.find((c) => c.id === selectedId)!;

  return (
    <PageLayout>
      <BackButton to="/priorities" />
      <PageHeader title="Your Career Recommendations" subtitle=""/>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        {MOCK_RECOMMENDATIONS.map((career) => (
          <CareerCard key={career.id} career={career} isSelected={career.id === selectedId} onClick={() => setSelectedId(career.id)}/>
        ))}
      </div>

      <CareerDetail career={selected} />

      <div className="mt-8 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Bridge Your Skill Gaps
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-6">
          Recommended courses to reach your career goals
        </p>

        <div className="space-y-8">
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
    </PageLayout>
  );
}
