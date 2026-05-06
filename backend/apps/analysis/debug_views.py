"""
Temporary DEBUG-only HTTP endpoints to verify DB seeding and DSS similarity.

Remove this module and its URL routes before production (see ``urls.py``).
"""

from __future__ import annotations

import json
from collections import defaultdict

import numpy as np
from django.conf import settings
from django.db.models import Prefetch
from django.http import Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from apps.catalog.models import (
    Course,
    CourseSkill,
    Job,
    JobFrameworkAlternative,
    JobSkill,
    Skill,
)
from apps.dss.constants import skill_weights_from_levels
from apps.dss.similarity import skill_match_breakdown
from apps.dss.types import JobRequirements


def _require_debug() -> None:
    if not settings.DEBUG:
        raise Http404("Test API is only available when DEBUG=True.")


def _job_requirements_for_queryset(jobs) -> list[JobRequirements]:
    out: list[JobRequirements] = []
    for job in jobs:
        mandatory = frozenset(js.skill_id for js in job.job_skills.all())
        slot_map: dict[int, set[int]] = defaultdict(set)
        for fa in job.framework_alternatives.all():
            slot_map[int(fa.slot_index)].add(int(fa.skill_id))
        slots = tuple(frozenset(slot_map[k]) for k in sorted(slot_map))
        out.append(
            JobRequirements(
                job_id=int(job.pk),
                mandatory_skill_ids=mandatory,
                framework_slots=slots,
            )
        )
    return out


@require_GET
def test_catalog_stats(request):
    """Aggregate counts and small samples from seeded catalog tables."""
    _require_debug()
    sample_skills = list(
        Skill.objects.order_by("id").values_list("id", "name")[:8]
    )
    sample_jobs = list(
        Job.objects.order_by("id").values("id", "title", "demand_score", "avg_salary")[:5]
    )
    return JsonResponse(
        {
            "_note": "Remove /api/test/* debug routes before production.",
            "counts": {
                "skills": Skill.objects.count(),
                "jobs": Job.objects.count(),
                "job_skills": JobSkill.objects.count(),
                "job_framework_alternatives": JobFrameworkAlternative.objects.count(),
                "courses": Course.objects.count(),
                "course_skills": CourseSkill.objects.count(),
            },
            "samples": {
                "skills": [{"id": pk, "name": name} for pk, name in sample_skills],
                "jobs": sample_jobs,
            },
        }
    )


@require_GET
def test_cosine_example(request):
    """
    Static worked example for mandatory-only cosine (same formula as ``_mandatory_cosine``).

    Uses two mandatory skills with weights 0.6 and 0.9 vs ideal vector of ones.
    """
    _require_debug()
    u = np.array([0.6, 0.9], dtype=np.float64)
    ones = np.ones_like(u)
    dot = float(np.dot(u, ones))
    nu = float(np.linalg.norm(u))
    nj = float(np.linalg.norm(ones))
    cosine = dot / (nu * nj)

    interpretation = (
        "For mandatory skills only, we take the user's weights on those dimensions "
        "and compare them to a vector of 1s (fully meeting every mandatory skill). "
        "Cosine = (u · 1) / (||u|| · ||1||). It is clipped to [0, 1]. "
        "The overall skill_match_score combines (mandatory_cosine weighted by mandatory count) "
        "with per-framework-slot max user weights and divides by mandatory_count + slot_count."
    )

    return JsonResponse(
        {
            "_note": "Educational static example matching apps.dss.similarity._mandatory_cosine.",
            "interpretation": interpretation,
            "example": {
                "mandatory_skill_internal_ids_logical": ["skill_dimension_1", "skill_dimension_2"],
                "user_weights_aligned_to_those_dimensions": [0.6, 0.9],
                "ideal_job_targets_ones_vector": [1.0, 1.0],
                "dot_product_u_dot_ones": dot,
                "norm_user_vector": nu,
                "norm_ones_vector": nj,
                "cosine_similarity": float(np.clip(cosine, 0.0, 1.0)),
            },
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def test_similarity_preview(request):
    """
    POST JSON with either::

        {"skills": [{"skill_id": 12, "level": "intermediate"}, ...], "limit_jobs": 15}

    or raw weights::

        {"weights": {"12": 0.6, "34": 0.9}, "limit_jobs": 15}

    Returns ``skill_match_score`` and cosine breakdown rows for seeded jobs.
    """
    _require_debug()
    try:
        body = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    limit_jobs = body.get("limit_jobs", 25)
    try:
        limit_jobs = max(1, min(int(limit_jobs), 100))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "limit_jobs must be an integer"}, status=400)

    if "weights" in body and body["weights"]:
        weights_in = body["weights"]
        if not isinstance(weights_in, dict):
            return JsonResponse({"detail": "weights must be a JSON object"}, status=400)
        skill_weights = {int(k): float(v) for k, v in weights_in.items()}
    elif "skills" in body:
        skills_in = body["skills"]
        if not isinstance(skills_in, list):
            return JsonResponse({"detail": "skills must be a JSON array"}, status=400)
        raw: dict[int, object] = {}
        for item in skills_in:
            if not isinstance(item, dict):
                return JsonResponse({"detail": "Each skills[] item must be an object"}, status=400)
            sid = item.get("skill_id")
            if sid is None:
                return JsonResponse({"detail": "Each skills[] entry needs skill_id"}, status=400)
            sid_int = int(sid)
            w = item.get("weight")
            if isinstance(w, (int, float)) and type(w) is not bool:
                raw[sid_int] = float(w)
            else:
                raw[sid_int] = str(item.get("level", "beginner"))
        try:
            skill_weights = skill_weights_from_levels(raw)
        except ValueError as exc:
            return JsonResponse({"detail": str(exc)}, status=400)
    else:
        return JsonResponse(
            {"detail": "Provide `skills` array or numeric `weights` object"},
            status=400,
        )

    prefetch_js = Prefetch(
        "job_skills",
        queryset=JobSkill.objects.select_related("skill").order_by("skill_id"),
    )
    prefetch_fw = Prefetch(
        "framework_alternatives",
        queryset=JobFrameworkAlternative.objects.select_related("skill").order_by(
            "slot_index",
            "skill_id",
        ),
    )
    jobs = list(
        Job.objects.prefetch_related(prefetch_js, prefetch_fw).order_by("pk")[:limit_jobs]
    )
    requirements = _job_requirements_for_queryset(jobs)

    rows = []
    for jr, dj in zip(requirements, jobs, strict=True):
        br = skill_match_breakdown(jr, skill_weights)
        rows.append(
            {
                "job_id": dj.pk,
                "title": dj.title,
                "skill_match_score": br["score"],
                "mandatory_cosine": br["mandatory_cosine"],
                "mandatory_skill_count": br["mandatory_skill_count"],
                "framework_slot_count": br["framework_slot_count"],
                "slot_max_sum": br["slot_max_sum"],
                "numerator": br["numerator"],
                "denominator": br["denominator"],
                "no_requirements": br["no_requirements"],
            }
        )

    return JsonResponse(
        {
            "_note": "Remove /api/test/* debug routes before production.",
            "resolved_skill_weights": skill_weights,
            "limit_jobs": limit_jobs,
            "jobs_preview": rows,
        }
    )
