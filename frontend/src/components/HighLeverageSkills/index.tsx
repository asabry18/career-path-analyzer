import { BookOpen, Briefcase } from "lucide-react";
import type { InsightsHighLeverageSkill } from "../../types";

interface HighLeverageSkillsProps {
  skills: InsightsHighLeverageSkill[];
  jobCount: number;
}

export default function HighLeverageSkills({ skills, jobCount }: HighLeverageSkillsProps) {
  if (!skills.length) return null;

  const maxJobs = Math.max(...skills.map((skill) => skill.job_count), 1);

  return (
    <section className="rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
        Skills That Unlock the Most Careers
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 mb-5">
        Learn these first to keep the widest range of job options open across {jobCount} roles.
      </p>

      <div className="space-y-3">
        {skills.map((skill) => (
          <div key={skill.id} className="flex items-center gap-3">
            <div className="w-36 text-sm text-gray-700 dark:text-gray-300 capitalize truncate">
              {skill.name}
            </div>
            <div className="flex-1 h-2 rounded-full bg-gray-100 dark:bg-gray-800">
              <div
                className="h-2 rounded-full bg-indigo-500"
                style={{ width: `${(skill.job_count / maxJobs) * 100}%` }}
              />
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 shrink-0">
              <span className="inline-flex items-center gap-1">
                <Briefcase size={12} />
                {skill.job_count} jobs
              </span>
              <span className="inline-flex items-center gap-1">
                <BookOpen size={12} />
                {skill.course_count} courses
              </span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
