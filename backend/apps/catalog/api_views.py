from collections import defaultdict
import math

from django.db.models import Count, Prefetch
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.catalog.models import Course, CourseSkill, Job, JobFrameworkAlternative, JobSkill, Skill

from . import serializers


class SkillListView(generics.ListAPIView):
    """``GET`` — all skills (seed + referenced by jobs/courses)."""

    serializer_class = serializers.SkillSerializer
    pagination_class = None
    queryset = Skill.objects.all().order_by("name")


class JobListView(generics.ListAPIView):
    """``GET`` — all jobs with mandatory skills and OR framework slots."""

    serializer_class = serializers.JobListSerializer
    pagination_class = None

    queryset = (
        Job.objects.prefetch_related(
            Prefetch(
                "job_skills",
                queryset=JobSkill.objects.select_related("skill").order_by(
                    "skill__name",
                    "skill_id",
                ),
            ),
            Prefetch(
                "framework_alternatives",
                queryset=JobFrameworkAlternative.objects.select_related("skill").order_by(
                    "slot_index",
                    "skill__name",
                    "skill_id",
                ),
            ),
        )
        .all()
        .order_by("title")
    )


class CourseListView(generics.ListAPIView):
    """``GET`` — courses linked to skills (preview for seed verification)."""

    serializer_class = serializers.CourseListSerializer
    pagination_class = None

    queryset = Course.objects.prefetch_related(
        Prefetch(
            "course_skills",
            queryset=CourseSkill.objects.select_related("skill").order_by(
                "skill__name",
                "skill_id",
            ),
        )
    ).order_by("title")


def _percentile(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (len(sorted_vals) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    lower = float(sorted_vals[f])
    upper = float(sorted_vals[c])
    return lower + (upper - lower) * (k - f)


@api_view(["GET"])
@permission_classes([AllowAny])
def catalog_insights(request):
    salaries = [
        float(val)
        for val in Job.objects.exclude(avg_salary__isnull=True)
        .values_list("avg_salary", flat=True)
    ]
    salaries.sort()
    median = _percentile(salaries, 0.5)
    q1 = _percentile(salaries, 0.25)
    q3 = _percentile(salaries, 0.75)

    top_demanded = Job.objects.order_by("-demand_score", "-avg_salary")[:5]
    top_salary = Job.objects.order_by("-avg_salary", "-demand_score")[:5]

    skill_counts: dict[int, dict[str, object]] = defaultdict(lambda: {"name": "", "count": 0})
    for row in JobSkill.objects.values("skill_id", "skill__name").annotate(cnt=Count("id")):
        sid = int(row["skill_id"])
        skill_counts[sid]["name"] = row["skill__name"]
        skill_counts[sid]["count"] = int(skill_counts[sid]["count"]) + int(row["cnt"])

    for row in JobFrameworkAlternative.objects.values("skill_id", "skill__name").annotate(
        cnt=Count("id")
    ):
        sid = int(row["skill_id"])
        skill_counts[sid]["name"] = row["skill__name"]
        skill_counts[sid]["count"] = int(skill_counts[sid]["count"]) + int(row["cnt"])

    top_skills = [
        {
            "id": sid,
            "name": data["name"],
            "frequency": data["count"],
        }
        for sid, data in skill_counts.items()
    ]
    top_skills.sort(key=lambda x: (-int(x["frequency"]), str(x["name"]).lower()))

    top_courses = list(
        Course.objects.annotate(skill_count=Count("course_skills"))
        .order_by("-skill_count", "title")[:5]
        .values("id", "title", "provider", "skill_count")
    )
    top_providers = list(
        Course.objects.values("provider")
        .annotate(count=Count("id"))
        .order_by("-count", "provider")[:5]
    )

    return Response(
        {
            "job_count": Job.objects.count(),
            "median_salary": median,
            "salary_iqr": q3 - q1,
            "top_demanded_jobs": [
                {
                    "id": job.id,
                    "title": job.title,
                    "demand_score": job.demand_score,
                    "avg_salary": job.avg_salary,
                }
                for job in top_demanded
            ],
            "top_salary_jobs": [
                {
                    "id": job.id,
                    "title": job.title,
                    "demand_score": job.demand_score,
                    "avg_salary": job.avg_salary,
                }
                for job in top_salary
            ],
            "top_skills": top_skills[:10],
            "courses": {
                "total_courses": Course.objects.count(),
                "top_courses": top_courses,
                "top_providers": top_providers,
            },
        }
    )
