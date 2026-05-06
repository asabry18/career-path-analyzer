"""Unit tests for ``similarity.py`` — no Django."""

import numpy as np
import pytest

from apps.dss.constants import LEVEL_INTERMEDIATE, skill_weights_from_levels, validate_unit_weight
from apps.dss.similarity import (
    build_vocab_index,
    collect_skill_ids,
    skill_match_breakdown,
    skill_match_score,
    user_dense_vector,
)
from apps.dss.types import JobRequirements


@pytest.fixture
def vue_or_slot_job() -> JobRequirements:
    """
    Frontend OR slot: Vue alone satisfies alongside unrelated mandatory baseline.
    Matches plan example: Vue only fulfills the JS framework slot.
    """
    react, angular, vue = 101, 102, 103
    return JobRequirements(
        job_id=1,
        mandatory_skill_ids=frozenset({10}),  # e.g. html baseline
        framework_slots=(
            frozenset({react, angular, vue}),
        ),
    )


def test_collect_skill_ids_union():
    a = JobRequirements(1, frozenset({1, 2}), (frozenset({3}),))
    b = JobRequirements(2, frozenset({2, 4}), tuple())
    assert collect_skill_ids((a, b)) == frozenset({1, 2, 3, 4})


def test_user_dense_vector_clips_bounds():
    idx = build_vocab_index([5, 7])
    vec = user_dense_vector(idx, dim=2, user_skill_weights={5: -1.0, 7: 2.0})
    assert np.allclose(vec, np.array([0.0, 1.0]))


def test_or_slot_partial_vue_satisfies_slot(vue_or_slot_job):
    user = {
        10: 1.0,  # mandatory perfect
        103: LEVEL_INTERMEDIATE,  # Vue only
        101: 0.0,
        102: 0.0,
    }
    score = skill_match_score(vue_or_slot_job, user)
    n_m = 1
    n_f = 1
    expected = (n_m * 1.0 + LEVEL_INTERMEDIATE) / (n_m + n_f)
    assert score == pytest.approx(expected)


def test_or_slot_user_misses_every_framework_alternative():
    job = JobRequirements(
        job_id=2,
        mandatory_skill_ids=frozenset(),
        framework_slots=(
            frozenset({101, 102, 103}),
        ),
    )
    user = {104: 1.0}  # unrelated skill
    score = skill_match_score(job, user)
    assert score == pytest.approx(0.0)


def test_mandatory_zero_norm_guard():
    job = JobRequirements(
        job_id=3,
        mandatory_skill_ids=frozenset({1, 2}),
        framework_slots=tuple(),
    )
    user = {}
    assert skill_match_score(job, user) == pytest.approx(0.0)


def test_no_requirements_returns_one():
    job = JobRequirements(4, frozenset(), tuple())
    assert skill_match_score(job, {}) == 1.0


def test_combine_mandatory_and_slots():
    job = JobRequirements(
        job_id=5,
        mandatory_skill_ids=frozenset({10}),
        framework_slots=(
            frozenset({20, 21}),
        ),
    )
    user = {10: 1.0, 21: 0.6}
    score = skill_match_score(job, user)
    assert score == pytest.approx((1.0 * 1.0 + 0.6) / 2.0)


def test_constants_skill_weights_helpers():
    w = skill_weights_from_levels({1: "intermediate", 2: 0.42})
    assert w[1] == LEVEL_INTERMEDIATE
    assert w[2] == pytest.approx(0.42)
    with pytest.raises(ValueError):
        validate_unit_weight(3.9)


def test_skill_match_breakdown_matches_public_score():
    job = JobRequirements(
        job_id=9,
        mandatory_skill_ids=frozenset({1, 2}),
        framework_slots=(frozenset({8, 9}),),
    )
    user = {1: 0.5, 2: 0.5, 9: 0.8}
    bd = skill_match_breakdown(job, user)
    assert bd["score"] == pytest.approx(skill_match_score(job, user))
