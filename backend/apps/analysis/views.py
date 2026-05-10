from collections import defaultdict

from django.db.models import Prefetch
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.catalog.models import (
    Course,
    CourseSkill,
    Job,
    JobFrameworkAlternative,
    JobSkill,
    Skill,
)
from apps.dss.ahp import pairwise_from_priority_ranking
from apps.dss.constants import weight_from_skill_level
from apps.dss.pipeline import JobCatalogEntry, PipelineResult, run
from apps.dss.setcover import CourseInfo
from apps.dss.types import JobRequirements

from .serializers import (
    AnalyzeRequestSerializer,
    AnalyzeResponseSerializer,
    map_priority_ids_to_criteria,
)


def placeholder(request):
    return JsonResponse({"app": "analysis"})


def _load_jobs() -> tuple[list[JobCatalogEntry], dict[int, Job]]:
    """Load all catalog jobs into pipeline DTOs and keep Django objects for descriptions."""
    prefetch_js = Prefetch(
        "job_skills",
        queryset=JobSkill.objects.order_by("skill_id"),
    )
    prefetch_fw = Prefetch(
        "framework_alternatives",
        queryset=JobFrameworkAlternative.objects.order_by("slot_index", "skill_id"),
    )
    qs = Job.objects.prefetch_related(prefetch_js, prefetch_fw).order_by("pk")

    entries: list[JobCatalogEntry] = []
    job_map: dict[int, Job] = {}
    for job in qs:
        mandatory = frozenset(js.skill_id for js in job.job_skills.all())
        slot_buckets: dict[int, set[int]] = defaultdict(set)
        for fa in job.framework_alternatives.all():
            slot_buckets[int(fa.slot_index)].add(int(fa.skill_id))
        slots = tuple(frozenset(slot_buckets[k]) for k in sorted(slot_buckets))

        entries.append(JobCatalogEntry(
            job_id=int(job.pk),
            title=job.title,
            requirements=JobRequirements(
                job_id=int(job.pk),
                mandatory_skill_ids=mandatory,
                framework_slots=slots,
            ),
            avg_salary=float(job.avg_salary),
            demand_score=int(job.demand_score),
        ))
        job_map[int(job.pk)] = job
    return entries, job_map


def _load_courses() -> list[CourseInfo]:
    """Load all catalog courses into pipeline DTOs."""
    qs = Course.objects.prefetch_related(
        Prefetch("course_skills", queryset=CourseSkill.objects.order_by("skill_id"))
    ).order_by("pk")

    return [
        CourseInfo(
            course_id=int(c.pk),
            title=c.title,
            provider=c.provider,
            url=c.url,
            skill_ids=frozenset(cs.skill_id for cs in c.course_skills.all()),
        )
        for c in qs
    ]


def _resolve_skill_names(ids: set[int]) -> dict[int, str]:
    """Bulk-load skill names for a set of IDs."""
    if not ids:
        return {}
    bulk = Skill.objects.in_bulk(ids)
    return {sid: bulk[sid].name for sid in ids if sid in bulk}


def _build_response(result: PipelineResult, job_map: dict[int, Job], skill_names: dict[int, str]) -> dict:
    """Transform PipelineResult into the JSON shape for the response serializer."""
    ranked_jobs = []
    for rj in result.ranked_jobs:
        db_job = job_map.get(rj.job_id)
        missing = [
            {"skill_id": sid, "name": skill_names.get(sid, f"skill_{sid}")}
            for sid in rj.missing_mandatory_skill_ids
        ]
        opt_fw = []
        for gap in rj.optional_framework_gaps:
            alts = [
                {"skill_id": sid, "name": skill_names.get(sid, f"skill_{sid}")}
                for sid in sorted(gap.alternative_skill_ids)
            ]
            opt_fw.append({"slot_index": gap.slot_index, "alternatives": alts})

        ranked_jobs.append({
            "rank": rj.rank,
            "job_id": rj.job_id,
            "title": rj.title,
            "description": db_job.description if db_job else "",
            "topsis_score": rj.topsis_score,
            "skill_match_score": rj.skill_match_score,
            "avg_salary": rj.avg_salary,
            "demand_score": rj.demand_score,
            "learning_effort": rj.learning_effort,
            "missing_skills": missing,
            "optional_frameworks": opt_fw,
        })

    sc = result.set_cover
    course_skills_map: dict[int, list[dict]] = {}
    for ci in sc.selected_courses:
        course_skills_map[ci.course_id] = [
            {"skill_id": sid, "name": skill_names.get(sid, f"skill_{sid}")}
            for sid in sorted(ci.skill_ids)
        ]

    learning_plan = {
        "selected_courses": [
            {
                "course_id": ci.course_id,
                "title": ci.title,
                "provider": ci.provider,
                "url": ci.url,
                "skills": course_skills_map.get(ci.course_id, []),
            }
            for ci in sc.selected_courses
        ],
        "covered_skills": [
            {"skill_id": sid, "name": skill_names.get(sid, f"skill_{sid}")}
            for sid in sorted(sc.covered_skill_ids)
        ],
        "uncovered_skills": [
            {"skill_id": sid, "name": skill_names.get(sid, f"skill_{sid}")}
            for sid in sorted(sc.uncovered_skill_ids)
        ],
        "solver_status": sc.solver_status,
    }

    return {
        "ahp": {
            "weights": result.ahp.weights,
            "lambda_max": result.ahp.lambda_max,
            "consistency_ratio": result.ahp.consistency_ratio,
            "consistency_ok": result.ahp.consistency_ratio <= 0.1,
        },
        "ranked_jobs": ranked_jobs,
        "learning_plan": learning_plan,
        "meta": {
            "vocab_size": result.vocab_size,
            "jobs_evaluated": result.jobs_evaluated,
            "jobs_after_threshold": result.jobs_after_threshold,
        },
    }


@api_view(["POST"])
def analyze(request):
    """
    ``POST /api/analyze/`` — run the full DSS pipeline.

    Accepts user skills (by name + level) and priority ranking, returns
    ranked jobs with skill gaps and a learning plan.
    """
    req_ser = AnalyzeRequestSerializer(data=request.data)
    if not req_ser.is_valid():
        return Response(req_ser.errors, status=status.HTTP_400_BAD_REQUEST)

    data = req_ser.validated_data
    skills_input = data["skills"]
    priority_ids = data["priorities"]
    threshold = data["threshold"]

    # ── Resolve skill names → IDs ────────────────────────────────────
    skill_name_to_obj: dict[str, Skill] = {}
    unknown_names: list[str] = []
    for item in skills_input:
        name = item["name"]
        try:
            skill_name_to_obj[name] = Skill.objects.get(name__iexact=name)
        except Skill.DoesNotExist:
            unknown_names.append(name)

    if unknown_names:
        return Response(
            {"detail": f"Unknown skills: {', '.join(unknown_names)}. "
                        "Check GET /api/skills/ for valid names."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # ── Build user_weights: skill_id → numeric weight ────────────────
    user_weights: dict[int, float] = {}
    for item in skills_input:
        skill_obj = skill_name_to_obj[item["name"]]
        user_weights[skill_obj.pk] = weight_from_skill_level(item["level"])

    # ── Convert priority ranking → AHP pairwise entries ──────────────
    criteria_order = map_priority_ids_to_criteria(priority_ids)
    pairwise = pairwise_from_priority_ranking(criteria_order)

    # ── Load catalog ─────────────────────────────────────────────────
    jobs, job_map = _load_jobs()
    courses = _load_courses()

    # ── Run pipeline ─────────────────────────────────────────────────
    try:
        result: PipelineResult = run(
            jobs=jobs,
            user_weights=user_weights,
            pairwise=pairwise,
            threshold=threshold,
            courses=courses,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    # ── Resolve all skill IDs to names for the response ──────────────
    all_skill_ids: set[int] = set(user_weights.keys())
    for rj in result.ranked_jobs:
        all_skill_ids.update(rj.missing_mandatory_skill_ids)
        for gap in rj.optional_framework_gaps:
            all_skill_ids.update(gap.alternative_skill_ids)
    all_skill_ids.update(result.set_cover.covered_skill_ids)
    all_skill_ids.update(result.set_cover.uncovered_skill_ids)
    for ci in result.set_cover.selected_courses:
        all_skill_ids.update(ci.skill_ids)
    skill_names = _resolve_skill_names(all_skill_ids)

    resp_data = _build_response(result, job_map, skill_names)
    return Response(resp_data, status=status.HTTP_200_OK)
