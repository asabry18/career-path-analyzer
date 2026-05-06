from django.db.models import Prefetch
from rest_framework import generics

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
