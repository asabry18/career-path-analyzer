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


def _split_sectors(sector: str | None) -> list[str]:
    if not sector or not sector.strip():
        return []
    return [part.strip() for part in sector.split(",") if part.strip()]


_MERGED_SECTORS = {"Business": "Software", "Design": "Software"}


def _normalize_insight_sector(sector: str) -> str:
    return _MERGED_SECTORS.get(sector, sector)


def _insight_sectors_for_job(sector: str | None) -> set[str]:
    return {_normalize_insight_sector(name) for name in _split_sectors(sector)}


_SPOTLIGHT_LIMIT = 3
_KEY_SKILLS_LIMIT = 4
_HIGH_LEVERAGE_LIMIT = 10
_ENTRY_ROLES_PER_SECTOR = 2


def _parse_salary_band(description: str) -> str | None:
    prefix = "Salary band: "
    if description and description.startswith(prefix):
        return description[len(prefix) :].strip()
    return None


def _build_job_snapshots(jobs: list[Job]) -> list[dict]:
    snapshots: list[dict] = []
    for job in jobs:
        mandatory = list(job.job_skills.all())
        framework = list(job.framework_alternatives.all())
        slot_indices = {fa.slot_index for fa in framework}
        key_skills = sorted(
            (js.skill.name for js in mandatory),
            key=str.lower,
        )[:_KEY_SKILLS_LIMIT]
        snapshots.append(
            {
                "id": job.id,
                "title": job.title,
                "demand_score": job.demand_score,
                "avg_salary": float(job.avg_salary),
                "sector": job.sector,
                "skill_count": len(mandatory) + len(slot_indices),
                "salary_band": _parse_salary_band(job.description or ""),
                "key_skills": key_skills,
            }
        )
    return snapshots


def _build_priority_spotlights(snapshots: list[dict]) -> dict[str, list[dict]]:
    if not snapshots:
        return {"salary": [], "demand": [], "easy_entry": [], "balance": []}

    max_demand = max(s["demand_score"] for s in snapshots) or 1
    max_salary = max(s["avg_salary"] for s in snapshots) or 1
    max_skills = max(s["skill_count"] for s in snapshots) or 1

    balance_scored: list[tuple[float, dict]] = []
    for snap in snapshots:
        score = (
            snap["demand_score"] / max_demand
            + snap["avg_salary"] / max_salary
            + (1 - snap["skill_count"] / max_skills)
        )
        balance_scored.append((score, snap))

    return {
        "salary": sorted(
            snapshots,
            key=lambda row: (-row["avg_salary"], -row["demand_score"]),
        )[:_SPOTLIGHT_LIMIT],
        "demand": sorted(
            snapshots,
            key=lambda row: (-row["demand_score"], -row["avg_salary"]),
        )[:_SPOTLIGHT_LIMIT],
        "easy_entry": sorted(
            snapshots,
            key=lambda row: (row["skill_count"], -row["demand_score"]),
        )[:_SPOTLIGHT_LIMIT],
        "balance": [
            snap
            for _, snap in sorted(balance_scored, key=lambda pair: -pair[0])[
                :_SPOTLIGHT_LIMIT
            ]
        ],
    }


def _build_entry_roles_by_sector(
    snapshots: list[dict],
    limit_per_sector: int = _ENTRY_ROLES_PER_SECTOR,
) -> list[dict]:
    by_sector: dict[str, list[dict]] = defaultdict(list)
    for snap in snapshots:
        for sector in _insight_sectors_for_job(snap.get("sector")):
            by_sector[sector].append(snap)

    result: list[dict] = []
    for sector in sorted(by_sector.keys()):
        roles = sorted(
            by_sector[sector],
            key=lambda row: (row["skill_count"], -row["demand_score"]),
        )[:limit_per_sector]
        result.append({"sector": sector, "roles": roles})
    return result


def _build_high_leverage_skills(limit: int = _HIGH_LEVERAGE_LIMIT) -> list[dict]:
    job_counts = {
        int(row["skill_id"]): int(row["job_count"])
        for row in JobSkill.objects.values("skill_id")
        .annotate(job_count=Count("job_id", distinct=True))
    }
    course_counts = {
        int(row["skill_id"]): int(row["course_count"])
        for row in CourseSkill.objects.values("skill_id")
        .annotate(course_count=Count("course_id", distinct=True))
    }

    rows: list[dict] = []
    for skill in Skill.objects.filter(id__in=job_counts.keys()):
        rows.append(
            {
                "id": skill.id,
                "name": skill.name,
                "job_count": job_counts.get(skill.id, 0),
                "course_count": course_counts.get(skill.id, 0),
            }
        )
    rows.sort(key=lambda row: (-int(row["job_count"]), str(row["name"]).lower()))
    return rows[:limit]


def _build_sector_insights(jobs: list[Job]) -> list[dict]:
    buckets: dict[str, dict] = defaultdict(
        lambda: {
            "job_count": 0,
            "total_demand": 0,
            "salaries": [],
            "top_job": None,
        }
    )

    for job in jobs:
        sectors = _insight_sectors_for_job(job.sector)
        if not sectors:
            continue
        for name in sectors:
            bucket = buckets[name]
            bucket["job_count"] += 1
            bucket["total_demand"] += int(job.demand_score)
            bucket["salaries"].append(float(job.avg_salary))
            current_top = bucket["top_job"]
            if current_top is None or int(job.demand_score) > int(current_top["demand_score"]):
                bucket["top_job"] = {
                    "id": job.id,
                    "title": job.title,
                    "demand_score": job.demand_score,
                    "avg_salary": job.avg_salary,
                }

    sectors = []
    for name, bucket in buckets.items():
        salaries = bucket["salaries"]
        sectors.append(
            {
                "name": name,
                "job_count": bucket["job_count"],
                "total_demand": bucket["total_demand"],
                "avg_salary": sum(salaries) / len(salaries) if salaries else 0.0,
                "top_job": bucket["top_job"],
            }
        )

    sectors.sort(key=lambda row: (-int(row["total_demand"]), row["name"].lower()))
    return sectors


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
    jobs_qs = Job.objects.prefetch_related(
        Prefetch(
            "job_skills",
            queryset=JobSkill.objects.select_related("skill"),
        ),
        Prefetch(
            "framework_alternatives",
            queryset=JobFrameworkAlternative.objects.select_related("skill"),
        ),
    )
    all_jobs = list(jobs_qs)
    snapshots = _build_job_snapshots(all_jobs)

    salaries = sorted(float(snap["avg_salary"]) for snap in snapshots)
    median = _percentile(salaries, 0.5)
    q1 = _percentile(salaries, 0.25)
    q3 = _percentile(salaries, 0.75)

    sector_jobs = [job for job in all_jobs if job.sector]
    sectors = _build_sector_insights(sector_jobs)
    priority_spotlights = _build_priority_spotlights(snapshots)
    entry_roles_by_sector = _build_entry_roles_by_sector(snapshots)
    high_leverage_skills = _build_high_leverage_skills()
    demand_salary_jobs = sorted(
        snapshots,
        key=lambda row: (-row["demand_score"], -row["avg_salary"]),
    )

    return Response(
        {
            "job_count": len(snapshots),
            "median_salary": median,
            "salary_iqr": q3 - q1,
            "sectors": sectors,
            "priority_spotlights": priority_spotlights,
            "entry_roles_by_sector": entry_roles_by_sector,
            "high_leverage_skills": high_leverage_skills,
            "demand_salary_jobs": demand_salary_jobs,
            "top_demanded_jobs": priority_spotlights["demand"],
            "top_salary_jobs": priority_spotlights["salary"],
            "top_skills": [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "frequency": row["job_count"],
                }
                for row in high_leverage_skills
            ],
            "courses": {
                "total_courses": Course.objects.count(),
                "top_courses": [],
                "top_providers": [],
            },
        }
    )
