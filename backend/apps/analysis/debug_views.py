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
from apps.dss.constants import (
    CRITERIA_KEYS,
    LEVEL_ADVANCED,
    LEVEL_ABOVE_AVERAGE,
    LEVEL_BEGINNER,
    LEVEL_AVERAGE,
    LEVEL_UNDER_AVERAGE,
    skill_weights_from_levels,
)
from apps.dss.similarity import build_vocab_skill_ids_ordered, skill_match_breakdown
from apps.dss.ahp import PairwiseEntry, run_ahp
from apps.dss.topsis import run_topsis
from apps.dss.types import JobRequirements


def _resolved_skill_rows(skill_weights: dict[int, float]) -> list[dict[str, object]]:
    """Join resolved numeric weights with catalog ``Skill.name`` for debugging."""
    if not skill_weights:
        return []
    bulk = Skill.objects.in_bulk(skill_weights.keys())
    rows: list[dict[str, object]] = []
    for sid in sorted(skill_weights.keys()):
        sk = bulk.get(sid)
        rows.append(
            {
                "skill_id": int(sid),
                "skill_name": sk.name if sk else None,
                "weight": float(skill_weights[sid]),
            }
        )
    return rows


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
        "Dense cosine on a fixed master vocabulary (scenario): binary job vector j "
        "(1 for each required skill) and sparse user weights u share the same axis order; "
        "similarity = (u · j) / (‖u‖ × ‖j‖). Dimensions where j=0 add 0 to the dot product; "
        "every dimension where u≠0 contributes to ‖u‖."
    )

    return JsonResponse(
        {
            "_note": "Educational numeric example matching apps.dss.similarity.dense_cosine_from_vectors.",
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

        {"skills": [{"skill_id": 12, "level": "average"}, ...], "limit_jobs": 15}

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
        skills_echo = None
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
        skills_echo = skills_in
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
    vocab_tuple = build_vocab_skill_ids_ordered(requirements, skill_weights)

    rows = []
    for jr, dj in zip(requirements, jobs, strict=True):
        br = skill_match_breakdown(
            jr, skill_weights, vocab_skill_ids_ordered=vocab_tuple
        )
        rows.append(
            {
                "job_id": dj.pk,
                "title": dj.title,
                "skill_match_score": br["score"],
                "dot_product_u_dot_j": br["dot_product_u_dot_j"],
                "norm_user_vector": br["norm_user_vector"],
                "norm_job_binary_vector": br["norm_job_binary_vector"],
                "job_binary_skill_count": br["job_binary_skill_count"],
                "vocab_dimension": br["vocab_dimension"],
                "no_requirements": br["no_requirements"],
            }
        )

    resolved_rows = _resolved_skill_rows(skill_weights)
    return JsonResponse(
        {
            "_note": "Remove /api/test/* debug routes before production.",
            "skills_payload_echo": skills_echo,
            "resolved_skill_weights": skill_weights,
            "user_skills_resolved": resolved_rows,
            "level_to_weight_reference": {
                "beginner": LEVEL_BEGINNER,
                "under average": LEVEL_UNDER_AVERAGE,
                "average": LEVEL_AVERAGE,
                "above average": LEVEL_ABOVE_AVERAGE,
                "advanced": LEVEL_ADVANCED,
            },
            "scenario_vocab_size": len(vocab_tuple),
            "limit_jobs": limit_jobs,
            "jobs_preview": rows,
        }
    )


def _framework_slot_learning_and_optional(
    job: Job,
    user_weights: dict[int, float],
    skill_bulk: dict[int, Skill],
) -> tuple[int, list[dict[str, object]]]:
    """
    Count framework slots with max user weight 0 (each counts 1 toward learning effort).
    Return optional_frameworks entries with real DB ``slot_index`` values.
    """
    slot_map: dict[int, set[int]] = defaultdict(set)
    for fa in job.framework_alternatives.all():
        slot_map[int(fa.slot_index)].add(int(fa.skill_id))
    optional_fw: list[dict[str, object]] = []
    unmatched_slots = 0
    for slot_index in sorted(slot_map.keys()):
        skills_in_slot = slot_map[slot_index]
        mx = max(
            (float(user_weights.get(sid, 0.0)) for sid in skills_in_slot),
            default=0.0,
        )
        if mx <= 0.0:
            unmatched_slots += 1
            alts: list[dict[str, object]] = []
            for sid in sorted(skills_in_slot):
                sk_obj = skill_bulk.get(sid)
                alts.append(
                    {
                        "skill_id": sid,
                        "name": sk_obj.name if sk_obj else None,
                    }
                )
            optional_fw.append({"slot_index": slot_index, "alternatives": alts})
    return unmatched_slots, optional_fw


@csrf_exempt
@require_http_methods(["POST"])
def test_pipeline_preview(request):
    """
    Full DSS path for local testing: skill match → threshold → decision matrix
    (SkillMatch, Salary, Demand, LearningEffort) → AHP weights → TOPSIS ranking.

    POST JSON::

        {
          "skills": [...] or "weights": {"12": 0.6},
          "pairwise": [ { "a": "skill_match", "b": "salary", "value": 3 }, ... 6 total ],
          "threshold": 0.3,
          "limit_jobs": 25
        }

    ``learning_effort`` = count(mandatory skills with user weight 0)
    + count(framework slots where max alternative weight is 0).
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

    threshold_raw = body.get("threshold", 0.3)
    try:
        threshold = float(threshold_raw)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "threshold must be a number"}, status=400)

    pairwise = body.get("pairwise")
    if not isinstance(pairwise, list):
        return JsonResponse(
            {"detail": "`pairwise` must be an array of 6 criterion comparisons"},
            status=400,
        )

    if "weights" in body and body["weights"]:
        weights_in = body["weights"]
        if not isinstance(weights_in, dict):
            return JsonResponse({"detail": "weights must be a JSON object"}, status=400)
        skill_weights = {int(k): float(v) for k, v in weights_in.items()}
        skills_echo = None
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
        skills_echo = skills_in
    else:
        return JsonResponse(
            {"detail": "Provide `skills` array or numeric `weights` object"},
            status=400,
        )

    try:
        ahp = run_ahp(pairwise)
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

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
    vocab_tuple = build_vocab_skill_ids_ordered(requirements, skill_weights)

    all_skill_ids: set[int] = set(skill_weights.keys())
    for jr in requirements:
        all_skill_ids |= jr.mandatory_skill_ids
        for slot in jr.framework_slots:
            all_skill_ids |= slot
    skill_bulk = Skill.objects.in_bulk(all_skill_ids)

    candidates: list[dict[str, object]] = []
    for jr, dj in zip(requirements, jobs, strict=True):
        breakdown = skill_match_breakdown(
            jr, skill_weights, vocab_skill_ids_ordered=vocab_tuple
        )
        skill_match_score = float(breakdown["score"])
        if skill_match_score < threshold:
            continue

        missing_mandatory = sorted(
            sid
            for sid in jr.mandatory_skill_ids
            if float(skill_weights.get(sid, 0.0)) <= 0.0
        )
        slot_extra, optional_fw = _framework_slot_learning_and_optional(
            dj, skill_weights, skill_bulk
        )
        learning_effort = len(missing_mandatory) + slot_extra
        missing_rows = []
        for sid in missing_mandatory:
            sk = skill_bulk.get(sid)
            missing_rows.append(
                {
                    "skill_id": sid,
                    "skill_name": sk.name if sk else None,
                }
            )

        candidates.append(
            {
                "job_id": int(dj.pk),
                "title": dj.title,
                "skill_match_score": skill_match_score,
                "salary": float(dj.avg_salary),
                "demand_score": int(dj.demand_score),
                "learning_effort": learning_effort,
                "missing_skills": missing_rows,
                "optional_frameworks": optional_fw,
            }
        )

    resolved_rows = _resolved_skill_rows(skill_weights)
    base_meta: dict[str, object] = {
        "_note": "DEBUG: similarity → threshold → AHP → TOPSIS. Remove before production.",
        "skills_payload_echo": skills_echo,
        "user_skills_resolved": resolved_rows,
        "level_to_weight_reference": {
            "beginner": LEVEL_BEGINNER,
                "under average": LEVEL_UNDER_AVERAGE,
                "average": LEVEL_AVERAGE,
                "above average": LEVEL_ABOVE_AVERAGE,
                "advanced": LEVEL_ADVANCED,
        },
        "scenario_vocab_size": len(vocab_tuple),
        "limit_jobs": limit_jobs,
        "jobs_evaluated": len(jobs),
        "threshold": threshold,
        "jobs_after_threshold": len(candidates),
        "ahp": {
            "weights": ahp.weights,
            "lambda_max": ahp.lambda_max,
            "consistency_ratio": ahp.consistency_ratio,
            "consistency_warning": ahp.consistency_ratio > 0.1,
            "criteria_order": list(CRITERIA_KEYS),
        },
    }

    if not candidates:
        base_meta["ranked_jobs"] = []
        base_meta["detail"] = (
            "No jobs met skill_match >= threshold. Lower `threshold` (e.g. 0.0) or add skills."
        )
        return JsonResponse(base_meta, status=200)

    matrix_rows = []
    for c in candidates:
        matrix_rows.append(
            [
                float(c["skill_match_score"]),
                float(c["salary"]),
                float(c["demand_score"]),
                float(c["learning_effort"]),
            ]
        )
    x = np.array(matrix_rows, dtype=np.float64)
    weights_vec = np.array([ahp.weights[k] for k in CRITERIA_KEYS], dtype=np.float64)
    topsis = run_topsis(
        x,
        weights_vec,
        is_cost=[
            False,
            False,
            False,
            True,
        ],
    )

    ranked_jobs: list[dict[str, object]] = []
    for rank_idx, flat_pos in enumerate(topsis.ranked_indices.tolist(), start=1):
        base = candidates[flat_pos]
        ranked_jobs.append(
            {
                "rank": rank_idx,
                "job_id": base["job_id"],
                "title": base["title"],
                "topsis_score": float(topsis.closeness[flat_pos]),
                "skill_match_score": base["skill_match_score"],
                "avg_salary": base["salary"],
                "demand_score": base["demand_score"],
                "learning_effort": base["learning_effort"],
                "missing_skills": base["missing_skills"],
                "optional_frameworks": base["optional_frameworks"],
            }
        )

    base_meta["topsis"] = {
        "positive_ideal": topsis.positive_ideal.tolist(),
        "negative_ideal": topsis.negative_ideal.tolist(),
    }
    base_meta["ranked_jobs"] = ranked_jobs
    return JsonResponse(base_meta)
