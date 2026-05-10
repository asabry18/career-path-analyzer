"""Unit tests for ``similarity.py`` — dense cosine on a global vocab (scenario)."""

import numpy as np
import pytest

from apps.dss.constants import LEVEL_INTERMEDIATE, skill_weights_from_levels, validate_unit_weight
from apps.dss.similarity import (
    build_vocab_index,
    build_vocab_skill_ids_ordered,
    collect_skill_ids,
    dense_cosine_from_vectors,
    job_relaxed_binary_vector,
    skill_match_breakdown,
    skill_match_score,
    skill_match_scores_for_jobs,
    user_dense_vector,
)
from apps.dss.types import JobRequirements


@pytest.fixture
def vue_or_slot_job() -> JobRequirements:
    react, angular, vue = 101, 102, 103
    return JobRequirements(
        job_id=1,
        mandatory_skill_ids=frozenset({10}),
        framework_slots=(
            frozenset({react, angular, vue}),
        ),
    )


def V(*skill_ids: int) -> tuple[int, ...]:
    return tuple(sorted(set(skill_ids)))


def test_collect_skill_ids_union():
    a = JobRequirements(1, frozenset({1, 2}), (frozenset({3}),))
    b = JobRequirements(2, frozenset({2, 4}), tuple())
    assert collect_skill_ids((a, b)) == frozenset({1, 2, 3, 4})


def test_build_vocab_ordered_union_user_and_jobs():
    jobs = [
        JobRequirements(1, frozenset({5, 9}), tuple()),
        JobRequirements(2, frozenset({9, 11}), (frozenset({20}),)),
    ]
    user = {5: 0.5, 99: 0.2}
    v = build_vocab_skill_ids_ordered(jobs, user)
    assert v == tuple(sorted({5, 9, 11, 20, 99}))


def test_user_dense_vector_clips_bounds():
    idx = build_vocab_index([5, 7])
    vec = user_dense_vector(idx, dim=2, user_skill_weights={5: -1.0, 7: 2.0})
    assert np.allclose(vec, np.array([0.0, 1.0]))


def test_or_slot_relaxed_binary_includes_framework_skills(vue_or_slot_job):
    voc = V(10, 101, 102, 103)
    bd = skill_match_breakdown(vue_or_slot_job, {}, vocab_skill_ids_ordered=voc)
    assert bd["job_binary_skill_count"] == 4
    user = {10: 1.0, 103: LEVEL_INTERMEDIATE, 101: 0.0, 102: 0.0}
    ix = build_vocab_index(voc)
    u = user_dense_vector(ix, len(voc), user)
    j = job_relaxed_binary_vector(vue_or_slot_job, ix, len(voc))
    expected = dense_cosine_from_vectors(u, j)
    score = skill_match_score(vue_or_slot_job, user, vocab_skill_ids_ordered=voc)
    assert score == pytest.approx(expected)


def test_or_slot_user_misses_every_framework_alternative():
    job = JobRequirements(
        job_id=2,
        mandatory_skill_ids=frozenset(),
        framework_slots=(frozenset({101, 102, 103}),),
    )
    voc = V(101, 102, 103, 104)
    user = {104: 1.0}
    assert skill_match_score(job, user, vocab_skill_ids_ordered=voc) == pytest.approx(0.0)


def test_user_zero_norm_returns_zero():
    job = JobRequirements(3, frozenset({1, 2}), tuple())
    voc = V(1, 2)
    assert skill_match_score(job, {}, vocab_skill_ids_ordered=voc) == pytest.approx(0.0)


def test_job_with_no_skill_bits_returns_cosine_one():
    job = JobRequirements(4, frozenset(), tuple())
    assert skill_match_breakdown(job, {}, vocab_skill_ids_ordered=V())["score"] == 1.0


def test_workbook_style_dense_cosine_data_analyst_and_backend_equal():
    """
    Steps 6–7 from the pedagogical workbook: full user ‖u‖ counts all declared skills.

    Backend Developer overlaps the same weight multiset {0.6, 0.9, 0.3} across three job
    ones as Data Analyst, so dense cosine coincides.

    Frontend Developer aligns only partially (HTML-only overlap among FE triple).
    """
    names = (
        "Python",
        "SQL",
        "Excel",
        "ML",
        "TensorFlow",
        "Node.js",
        "HTML",
        "CSS",
        "JavaScript",
        "Statistics",
        "Linux",
        "Docker",
        "AWS",
        "Networking",
        "Security",
        "Java",
        "Kotlin",
        "Android",
        "Power BI",
        "Communication",
        "Testing",
        "Automation",
    )
    nmap = {n: i + 1 for i, n in enumerate(names)}

    def jb(*keys: str) -> frozenset[int]:
        return frozenset(nmap[k] for k in keys)

    jobs = (
        JobRequirements(1, jb("Python", "SQL", "Excel"), tuple()),
        JobRequirements(2, jb("Python", "SQL", "Node.js"), tuple()),
        JobRequirements(3, jb("HTML", "CSS", "JavaScript"), tuple()),
    )
    user = {
        nmap["Python"]: 0.6,
        nmap["SQL"]: 0.9,
        nmap["Excel"]: 0.3,
        nmap["HTML"]: 0.6,
        nmap["Node.js"]: 0.3,
    }
    vocab = build_vocab_skill_ids_ordered(jobs, user)
    s_da = skill_match_score(jobs[0], user, vocab_skill_ids_ordered=vocab)
    s_bd = skill_match_score(jobs[1], user, vocab_skill_ids_ordered=vocab)
    s_fe = skill_match_score(jobs[2], user, vocab_skill_ids_ordered=vocab)

    ix = build_vocab_index(vocab)
    dim = len(vocab)
    u = user_dense_vector(ix, dim, user)
    j_da = job_relaxed_binary_vector(jobs[0], ix, dim)
    manual_da = dense_cosine_from_vectors(u, j_da)

    assert s_da == pytest.approx(manual_da)
    assert s_da == pytest.approx(s_bd)
    assert s_da == pytest.approx(1.8 / (3**0.5 * 1.71**0.5), abs=5e-3)
    j_fe = job_relaxed_binary_vector(jobs[2], ix, dim)
    assert s_fe == pytest.approx(dense_cosine_from_vectors(u, j_fe))
    assert s_fe == pytest.approx(0.6 / ((3**0.5) * (1.71**0.5)), abs=5e-3)


def test_skill_match_scores_for_jobs_shared_vocab():
    a = JobRequirements(1, frozenset({1}), tuple())
    b = JobRequirements(2, frozenset({2}), tuple())
    out = skill_match_scores_for_jobs((a, b), {1: 0.5})
    voc = build_vocab_skill_ids_ordered((a, b), {1: 0.5})
    assert out[1] == pytest.approx(
        skill_match_score(a, {1: 0.5}, vocab_skill_ids_ordered=voc)
    )
    assert out[2] == pytest.approx(0.0)


def test_constants_skill_weights_helpers():
    w = skill_weights_from_levels({1: "intermediate", 2: 0.42})
    assert w[1] == LEVEL_INTERMEDIATE
    assert w[2] == pytest.approx(0.42)
    with pytest.raises(ValueError):
        validate_unit_weight(3.9)


def test_skill_match_breakdown_matches_public_score():
    job = JobRequirements(9, frozenset({1, 2}), (frozenset({8, 9}),))
    voc = V(1, 2, 8, 9)
    user = {1: 0.5, 2: 0.5, 9: 0.8}
    bd = skill_match_breakdown(job, user, vocab_skill_ids_ordered=voc)
    assert bd["score"] == pytest.approx(
        skill_match_score(job, user, vocab_skill_ids_ordered=voc)
    )
