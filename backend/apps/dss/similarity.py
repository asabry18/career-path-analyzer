"""
Skill match combining mandatory cosine alignment with per-slot max for frameworks.

Mandatory requirement vector is binary ones on mandatory skill dimensions; user
contributions follow the weighted ``u`` vector. Each framework slot counts as one
logical demand unit: its fulfillment is ``max_{t in slot} u_t`` in [0, 1].

The final ``skill_match_score`` blends mandatory cosine (weighted by mandatory
skill count) and slot maxima (summed across slots), divided by (#mandatory skills
+ #slots). Pure NumPy linear algebra aside from orchestration guards.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

import numpy as np

from apps.dss.types import JobRequirements


def collect_skill_ids(jobs: Iterable[JobRequirements]) -> frozenset[int]:
    ids: set[int] = set()
    for job in jobs:
        ids |= job.mandatory_skill_ids
        for slot in job.framework_slots:
            ids |= slot
    return frozenset(ids)


def build_vocab_index(skill_ids: Sequence[int]) -> dict[int, int]:
    """Stable index 0 .. n-1 for every skill ID in the union vocabulary."""
    return {sid: i for i, sid in enumerate(sorted(skill_ids))}


def user_dense_vector(
    skill_index: Mapping[int, int],
    dim: int,
    user_skill_weights: Mapping[int, float],
) -> np.ndarray:
    vec = np.zeros(dim, dtype=np.float64)
    for sid, w in user_skill_weights.items():
        idx = skill_index.get(sid)
        if idx is None:
            continue
        vec[idx] = float(w)
    np.clip(vec, 0.0, 1.0, out=vec)
    return vec


def _mandatory_cosine(
    user_weights_by_id: Mapping[int, float],
    mandatory_ids: Iterable[int],
) -> float:
    """
    Cosine similarity between the user's mandatory sub-vector and an all-ones target.

    Guards: empty mandatory ⇒ 1.0 (vacuous match); zero user norm ⇒ 0.0.
    """
    mids = sorted(set(mandatory_ids))
    if not mids:
        return 1.0
    u = np.array([float(user_weights_by_id.get(s, 0.0)) for s in mids], dtype=np.float64)
    ones = np.ones_like(u)
    nu = np.linalg.norm(u)
    nj = np.linalg.norm(ones)
    if nu <= 0.0 or nj <= 0.0:
        return 0.0
    cos = float(np.dot(u, ones) / (nu * nj))
    return float(np.clip(cos, 0.0, 1.0))


def _framework_slot_aggregate(
    user_weights_by_id: Mapping[int, float],
    framework_slots: tuple[frozenset[int], ...],
) -> tuple[float, int]:
    """
    Sum of ``max(users in slot)`` per slot — each slot is one unit capped at [0,1].
    Also returns slot count K (for denominators).
    """
    slot_max_sum = 0.0
    for slot in framework_slots:
        if not slot:
            continue
        vmax = max(float(user_weights_by_id.get(sid, 0.0)) for sid in slot)
        slot_max_sum += float(np.clip(vmax, 0.0, 1.0))
    return slot_max_sum, len(framework_slots)


def skill_match_score(
    job: JobRequirements,
    user_skill_weights: Mapping[int, float],
) -> float:
    """
    Single score in ``[0, 1]`` per plan Step 5.

    When there are neither mandatory skills nor slots, score is ``1.0``.
    """
    return float(skill_match_breakdown(job, user_skill_weights)["score"])


def skill_match_breakdown(
    job: JobRequirements,
    user_skill_weights: Mapping[int, float],
) -> dict[str, float | int]:
    """
    Numeric parts of :func:`skill_match_score` for debugging / API transparency.

    Keys are stable for JSON responses. ``score`` matches :func:`skill_match_score`.
    """
    n_m = len(job.mandatory_skill_ids)
    usable_slots = tuple(s for s in job.framework_slots if s)
    n_f = len(usable_slots)
    denom_f = float(n_m + n_f)
    if denom_f <= 0.0:
        return {
            "score": 1.0,
            "no_requirements": True,
            "mandatory_cosine": 1.0,
            "mandatory_skill_count": 0,
            "framework_slot_count": 0,
            "slot_max_sum": 0.0,
            "numerator": 0.0,
            "denominator": 0,
        }
    mand = _mandatory_cosine(user_skill_weights, job.mandatory_skill_ids)
    slot_sum, _ = _framework_slot_aggregate(user_skill_weights, usable_slots)
    numerator = float(n_m) * mand + slot_sum
    score = float(np.clip(numerator / denom_f, 0.0, 1.0))
    return {
        "score": score,
        "no_requirements": False,
        "mandatory_cosine": mand,
        "mandatory_skill_count": n_m,
        "framework_slot_count": n_f,
        "slot_max_sum": float(slot_sum),
        "numerator": float(numerator),
        "denominator": int(round(denom_f)),
    }


def skill_match_scores_for_jobs(
    jobs: Iterable[JobRequirements],
    user_skill_weights: Mapping[int, float],
) -> dict[int, float]:
    """Compute ``skill_match_score`` keyed by ``job_id``."""
    weights = {int(k): float(v) for k, v in user_skill_weights.items()}
    return {
        job.job_id: skill_match_score(job, weights)
        for job in jobs
    }
