import { BookOpen, ExternalLink } from "lucide-react";
import type { Course } from "../../types";

interface CourseCardProps {
  course: Course;
}

export default function CourseCard({ course }: CourseCardProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-gray-200
      dark:border-gray-700 bg-white dark:bg-gray-900 px-5 py-4">
      <div className="flex items-center gap-3 min-w-0">
        <BookOpen size={20} className="flex-shrink-0 text-gray-400 dark:text-gray-500" />
        <div className="min-w-0">
          <p className="font-medium text-gray-900 dark:text-white truncate">
            {course.title}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {course.platform} &bull; {course.duration}
          </p>
        </div>
      </div>

      <a href={course.url} target="_blank" rel="noopener noreferrer" className="flex-shrink-0 ml-4 flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
        View Course
        <ExternalLink size={14} />
      </a>
    </div>
  );
}
