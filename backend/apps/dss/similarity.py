"""
Skill match score = cosine similarity on a unified global skill vocabulary.

**Scenario (dense cosine)**

- Fixed ordered vocabulary IDs (typically ``sorted(...)`` union of skills from jobs and the user).
- **Job binary vector** ``j``: ``j[k] = 1`` where the skill is required—mandatory rows **or**
  **any framework alternative** (relaxed OR-bag encoding; each referenced skill contributes a dimension).
  Zeros elsewhere.
- **User vector** ``u``: declared weights ``[0,1]`` on chosen skills, zeros elsewhere.
- **Cosine**:
  ``similarity = (u · j) / (||u|| × ||j||)``.

Dots count only overlaps: extra unrelated user skills enlarge ``||u||`` but contribute **0**
to ``u · j``. Skills the job marks with ``0`` do not enlarge ``||u||``.
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


def build_vocab_skill_ids_ordered(
    jobs: Iterable[JobRequirements],
    user_skill_weights: Mapping[int, float],
) -> tuple[int, ...]:
    """
    Scenario “master skill list”: all skills appearing in evaluated jobs plus any the user declares.
    Stable order ``sorted(skill_id)``.
    """
    ids = set(collect_skill_ids(jobs))
    ids.update(int(k) for k in user_skill_weights.keys())
    return tuple(sorted(ids))


def build_vocab_index(skill_ids: Sequence[int]) -> dict[int, int]:
    return {sid: i for i, sid in enumerate(skill_ids)}


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


def job_relaxed_binary_vector(
    job: JobRequirements,
    skill_index: Mapping[int, int],
    dim: int,
) -> np.ndarray:
    """
    Binary job profile: mandatory AND every framework alternative carries weight 1
    over the shared vocab (relax-bag embedding for similarity).
    """
    vec = np.zeros(dim, dtype=np.float64)
    for sid in job.mandatory_skill_ids:
        hi = skill_index.get(sid)
        if hi is not None:
            vec[hi] = 1.0
    for slot in job.framework_slots:
        for sid in slot:
            hi = skill_index.get(sid)
            if hi is not None:
                vec[hi] = 1.0
    return vec


def dense_cosine_from_vectors(user_vec: np.ndarray, job_vec: np.ndarray) -> float:
    """``(u·j)/(||u||·||j||)`` clipped to ``[0,1]``. Handles zero-job / zero-user norms."""
    dot_val = float(np.dot(user_vec, job_vec))
    nu = float(np.linalg.norm(user_vec))
    nj = float(np.linalg.norm(job_vec))

    tol = 1e-18
    if nj <= tol:
        return 1.0
    if nu <= tol:
        return 0.0

    cos = dot_val / (nu * nj)
    return float(np.clip(cos, 0.0, 1.0))


def skill_match_breakdown(
    job: JobRequirements,
    user_skill_weights: Mapping[int, float],
    *,
    vocab_skill_ids_ordered: Sequence[int],
) -> dict[str, float | int | bool]:
    """
    ``score`` = dense cosine similarity (scenario Steps 6–7) on ``vocab_skill_ids_ordered``.
    """
    vocab = tuple(vocab_skill_ids_ordered)
    index = build_vocab_index(vocab)
    dim = len(vocab)
    if dim == 0:
        return {
            "score": 1.0,
            "no_requirements": True,
            "vocab_dimension": 0,
            "dot_product_u_dot_j": 0.0,
            "norm_user_vector": 0.0,
            "norm_job_binary_vector": 0.0,
            "job_binary_skill_count": 0,
        }

    weights = {int(k): float(v) for k, v in user_skill_weights.items()}
    user_vec = user_dense_vector(index, dim, weights)
    job_vec = job_relaxed_binary_vector(job, index, dim)

    dot_val = float(np.dot(user_vec, job_vec))
    nu = float(np.linalg.norm(user_vec))
    nj = float(np.linalg.norm(job_vec))

    score = dense_cosine_from_vectors(user_vec, job_vec)

    job_support = int(round(np.sum(job_vec)))
    return {
        "score": score,
        "no_requirements": job_support <= 0,
        "vocab_dimension": dim,
        "dot_product_u_dot_j": dot_val,
        "norm_user_vector": nu,
        "norm_job_binary_vector": nj,
        "job_binary_skill_count": job_support,
    }


def skill_match_score(
    job: JobRequirements,
    user_skill_weights: Mapping[int, float],
    *,
    vocab_skill_ids_ordered: Sequence[int],
) -> float:
    """Public score in ``[0,1]`` over the given vocabulary."""
    return float(
        skill_match_breakdown(
            job, user_skill_weights, vocab_skill_ids_ordered=vocab_skill_ids_ordered
        )["score"]
    )


def skill_match_scores_for_jobs(
    jobs: Iterable[JobRequirements],
    user_skill_weights: Mapping[int, float],
    *,
    vocab_skill_ids_ordered: Sequence[int] | None = None,
) -> dict[int, float]:
    """
    Computes ``skill_match_score`` for each ``job.job_id``.
    Builds the scenario vocabulary unless ``vocab_skill_ids_ordered`` is provided.
    """
    job_list = list(jobs)
    weights = {int(k): float(v) for k, v in user_skill_weights.items()}
    vocab: tuple[int, ...]
    if vocab_skill_ids_ordered is None:
        vocab = build_vocab_skill_ids_ordered(job_list, weights)
    else:
        vocab = tuple(sorted(set(vocab_skill_ids_ordered)))
    return {
        job.job_id: skill_match_score(job, weights, vocab_skill_ids_ordered=vocab)
        for job in job_list
    }
