"""
Full DSS pipeline — pure Python, no Django imports.

    similarity → threshold → decision matrix → AHP → TOPSIS
    → missing_skills + optional_frameworks → Set Cover
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np

from apps.dss.ahp import AhpResult, PairwiseEntry, run_ahp
from apps.dss.constants import CRITERIA_KEYS
from apps.dss.setcover import CourseInfo, SetCoverResult, solve_set_cover
from apps.dss.similarity import (
    build_vocab_skill_ids_ordered,
    skill_match_breakdown,
    skill_match_score,
)
from apps.dss.topsis import TopsisResult, run_topsis
from apps.dss.types import JobRequirements


# ------------------------------------------------------------------
# Input / output data types
# ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class JobCatalogEntry:
    """One job from the DB, flattened for the pipeline."""

    job_id: int
    title: str
    requirements: JobRequirements
    avg_salary: float
    demand_score: int


@dataclass(frozen=True, slots=True)
class FrameworkSlotGap:
    """An OR slot the user has not satisfied (max weight = 0)."""

    slot_index: int
    alternative_skill_ids: frozenset[int]


@dataclass(frozen=True, slots=True)
class RankedJob:
    """One row in the final output."""

    rank: int
    job_id: int
    title: str
    topsis_score: float
    skill_match_score: float
    avg_salary: float
    demand_score: int
    learning_effort: int
    missing_mandatory_skill_ids: list[int]
    optional_framework_gaps: list[FrameworkSlotGap]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Everything the analyze endpoint needs to serialize."""

    ahp: AhpResult
    ranked_jobs: list[RankedJob]
    topsis: TopsisResult | None
    set_cover: SetCoverResult
    vocab_size: int
    jobs_evaluated: int
    jobs_after_threshold: int


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _learning_effort(
    req: JobRequirements,
    user_weights: Mapping[int, float],
) -> int:
    missing = sum(
        1 for sid in req.mandatory_skill_ids
        if float(user_weights.get(sid, 0.0)) <= 0.0
    )
    for slot in req.framework_slots:
        mx = max(
            (float(user_weights.get(sid, 0.0)) for sid in slot),
            default=0.0,
        )
        if mx <= 0.0:
            missing += 1
    return missing


def _missing_mandatory(
    req: JobRequirements,
    user_weights: Mapping[int, float],
) -> list[int]:
    return sorted(
        sid for sid in req.mandatory_skill_ids
        if float(user_weights.get(sid, 0.0)) <= 0.0
    )


def _framework_gaps(
    req: JobRequirements,
    user_weights: Mapping[int, float],
) -> list[FrameworkSlotGap]:
    gaps: list[FrameworkSlotGap] = []
    for slot_idx, slot in enumerate(req.framework_slots):
        mx = max(
            (float(user_weights.get(sid, 0.0)) for sid in slot),
            default=0.0,
        )
        if mx <= 0.0:
            gaps.append(FrameworkSlotGap(
                slot_index=slot_idx,
                alternative_skill_ids=slot,
            ))
    return gaps


def _collect_all_missing_skill_ids(ranked_jobs: Sequence[RankedJob]) -> frozenset[int]:
    """Union of mandatory gaps + one representative skill per unmatched framework slot."""
    ids: set[int] = set()
    for rj in ranked_jobs:
        ids.update(rj.missing_mandatory_skill_ids)
        for gap in rj.optional_framework_gaps:
            if gap.alternative_skill_ids:
                ids.add(min(gap.alternative_skill_ids))
    return frozenset(ids)


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------


def run(
    *,
    jobs: Sequence[JobCatalogEntry],
    user_weights: Mapping[int, float],
    pairwise: Sequence[PairwiseEntry | Mapping[str, object]],
    threshold: float = 0.4,
    courses: Sequence[CourseInfo] = (),
) -> PipelineResult:
    """
    Execute the full DSS pipeline.

    Parameters
    ----------
    jobs : catalog jobs (already loaded from DB).
    user_weights : skill_id → weight in [0, 1].
    pairwise : exactly 6 Saaty comparisons between the 4 criteria.
    threshold : minimum skill_match_score to keep a job.
    courses : available courses for Set Cover (may be empty).
    """
    weights = {int(k): float(v) for k, v in user_weights.items()}
    job_reqs = [j.requirements for j in jobs]
    vocab = build_vocab_skill_ids_ordered(job_reqs, weights)

    ahp = run_ahp(list(pairwise))

    # --- Similarity + threshold ---
    candidates: list[tuple[JobCatalogEntry, float, int, list[int], list[FrameworkSlotGap]]] = []
    for entry in jobs:
        sc = skill_match_score(
            entry.requirements, weights,
            vocab_skill_ids_ordered=vocab,
        )
        if sc < threshold:
            continue
        le = _learning_effort(entry.requirements, weights)
        mm = _missing_mandatory(entry.requirements, weights)
        fg = _framework_gaps(entry.requirements, weights)
        candidates.append((entry, sc, le, mm, fg))

    if not candidates:
        return PipelineResult(
            ahp=ahp,
            ranked_jobs=[],
            topsis=None,
            set_cover=SetCoverResult(
                selected_courses=[],
                covered_skill_ids=frozenset(),
                uncovered_skill_ids=frozenset(),
                solver_status="Optimal",
            ),
            vocab_size=len(vocab),
            jobs_evaluated=len(jobs),
            jobs_after_threshold=0,
        )

    # --- Decision matrix ---
    matrix = np.array([
        [sc, entry.avg_salary, entry.demand_score, le]
        for entry, sc, le, _, _ in candidates
    ], dtype=np.float64)

    w_vec = np.array([ahp.weights[k] for k in CRITERIA_KEYS], dtype=np.float64)
    topsis = run_topsis(matrix, w_vec, is_cost=[False, False, False, True])

    ranked: list[RankedJob] = []
    for rank, idx in enumerate(topsis.ranked_indices.tolist(), start=1):
        entry, sc, le, mm, fg = candidates[idx]
        ranked.append(RankedJob(
            rank=rank,
            job_id=entry.job_id,
            title=entry.title,
            topsis_score=float(topsis.closeness[idx]),
            skill_match_score=sc,
            avg_salary=entry.avg_salary,
            demand_score=entry.demand_score,
            learning_effort=le,
            missing_mandatory_skill_ids=mm,
            optional_framework_gaps=fg,
        ))

    # --- Set Cover ---
    all_missing = _collect_all_missing_skill_ids(ranked)
    sc_result = solve_set_cover(all_missing, list(courses))

    return PipelineResult(
        ahp=ahp,
        ranked_jobs=ranked,
        topsis=topsis,
        set_cover=sc_result,
        vocab_size=len(vocab),
        jobs_evaluated=len(jobs),
        jobs_after_threshold=len(candidates),
    )
