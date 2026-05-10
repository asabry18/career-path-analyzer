"""Unit tests for AHP (pairwise matrix, weights, consistency ratio)."""

import numpy as np
import pytest

from apps.dss.ahp import (
    PairwiseEntry,
    build_pairwise_matrix,
    consistency_ratio,
    pairwise_from_priority_ranking,
    principal_eigenvector_weights,
    ri_for_n,
    run_ahp,
    run_ahp_from_matrix,
)


def test_ri_saaty_known_values() -> None:
    assert ri_for_n(3) == pytest.approx(0.58)
    assert ri_for_n(4) == pytest.approx(0.90)


def test_all_equal_importance_four_criteria() -> None:
    order = ["skill_match", "salary", "demand", "learning_effort"]
    pairs = []
    keys = order
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            pairs.append(PairwiseEntry(a=keys[i], b=keys[j], value=1.0))
    res = run_ahp(pairs, criteria_order=order)
    for k in order:
        assert res.weights[k] == pytest.approx(0.25)
    assert res.lambda_max == pytest.approx(4.0, abs=1e-5)
    assert res.consistency_ratio == pytest.approx(0.0, abs=1e-6)


def test_classic_three_criteria_example() -> None:
    """Textbook reciprocal 3×3 matrix; λ_max > n and reasonably consistent."""
    mat = np.array([[1.0, 2.0, 5.0], [0.5, 1.0, 3.0], [0.2, 1.0 / 3.0, 1.0]])
    keys = ["c1", "c2", "c3"]
    res = run_ahp_from_matrix(mat, criteria_order=keys)
    assert abs(sum(res.weights.values()) - 1.0) < 1e-6
    eig_max = float(np.max(np.real(np.linalg.eigvals(mat))))
    assert res.lambda_max == pytest.approx(eig_max, abs=1e-10)
    assert 3.0 < res.lambda_max < 3.01
    assert res.consistency_ratio < 0.1


def test_plan_style_pairwise_payload() -> None:
    """Six comparisons as in Part D API example (keys only)."""
    entries = [
        PairwiseEntry("skill_match", "salary", 3),
        PairwiseEntry("skill_match", "demand", 5),
        PairwiseEntry("skill_match", "learning_effort", 7),
        PairwiseEntry("salary", "demand", 3),
        PairwiseEntry("salary", "learning_effort", 5),
        PairwiseEntry("demand", "learning_effort", 3),
    ]
    res = run_ahp(entries)
    assert abs(sum(res.weights.values()) - 1.0) < 1e-9
    assert res.weights["skill_match"] >= res.weights["learning_effort"]


def test_dict_entries_equivalent() -> None:
    d = [{"a": "skill_match", "b": "salary", "value": 3}]
    pytest.raises(ValueError, lambda: build_pairwise_matrix(d))
    entries = [
        {"a": "skill_match", "b": "salary", "value": 3},
        {"a": "skill_match", "b": "demand", "value": 5},
        {"a": "skill_match", "b": "learning_effort", "value": 7},
        {"a": "salary", "b": "demand", "value": 3},
        {"a": "salary", "b": "learning_effort", "value": 5},
        {"a": "demand", "b": "learning_effort", "value": 3},
    ]
    assert run_ahp(entries).lambda_max > 4.0


def test_duplicate_pair_raises() -> None:
    entries = [
        PairwiseEntry("skill_match", "salary", 3),
        PairwiseEntry("salary", "skill_match", 2),
        PairwiseEntry("skill_match", "demand", 5),
        PairwiseEntry("skill_match", "learning_effort", 7),
        PairwiseEntry("salary", "demand", 3),
        PairwiseEntry("salary", "learning_effort", 5),
        PairwiseEntry("demand", "learning_effort", 3),
    ]
    with pytest.raises(ValueError, match="Duplicate"):
        run_ahp(entries)


def test_incomplete_pairwise_raises() -> None:
    entries = [PairwiseEntry("skill_match", "salary", 3)]
    with pytest.raises(ValueError, match="Expected 6"):
        run_ahp(entries)


def test_non_positive_value_raises() -> None:
    entries = [
        PairwiseEntry("skill_match", "salary", 0.0),
    ]
    with pytest.raises(ValueError, match="positive"):
        build_pairwise_matrix(entries)


def test_pairwise_from_priority_ranking_structure() -> None:
    """Ranked [salary, demand, skill_match, learning_effort] → 6 entries with correct intensities."""
    ranked = ["salary", "demand", "skill_match", "learning_effort"]
    entries = pairwise_from_priority_ranking(ranked)
    assert len(entries) == 6
    lookup = {(e.a, e.b): e.value for e in entries}
    assert lookup[("salary", "demand")] == 3
    assert lookup[("salary", "skill_match")] == 5
    assert lookup[("salary", "learning_effort")] == 7
    assert lookup[("demand", "skill_match")] == 3
    assert lookup[("demand", "learning_effort")] == 5
    assert lookup[("skill_match", "learning_effort")] == 3


def test_pairwise_from_priority_ranking_produces_consistent_ahp() -> None:
    """Generated pairwise entries should feed into run_ahp with CR < 0.1."""
    ranked = ["demand", "skill_match", "salary", "learning_effort"]
    entries = pairwise_from_priority_ranking(ranked)
    res = run_ahp(entries)
    assert res.consistency_ratio < 0.1
    assert res.weights["demand"] > res.weights["learning_effort"]
    assert abs(sum(res.weights.values()) - 1.0) < 1e-9


def test_principal_eigenvector_weights_column_mean_fallback_property() -> None:
    """Geometric mean method would differ slightly; eigenvector is spec (Part B)."""
    mat = np.array([[1.0, 3.0], [1.0 / 3.0, 1.0]])
    w, lam = principal_eigenvector_weights(mat)
    assert w.sum() == pytest.approx(1.0)
    assert lam == pytest.approx(2.0, abs=1e-5)
