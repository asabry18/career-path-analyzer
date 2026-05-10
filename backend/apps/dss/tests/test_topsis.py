"""Unit tests for TOPSIS (min–max, weighted ideal distances)."""

import numpy as np
import pytest

from apps.dss.topsis import min_max_transform, run_topsis


def test_min_max_benefit_only() -> None:
    x = np.array([[10.0, 2.0], [4.0, 5.0]])
    r = min_max_transform(x, is_cost=[False, False])
    assert r[0, 0] == pytest.approx(1.0)
    assert r[1, 0] == pytest.approx(0.0)
    assert r[0, 1] == pytest.approx(0.0)
    assert r[1, 1] == pytest.approx(1.0)


def test_min_max_cost_column() -> None:
    """Lower raw cost → higher score after transform."""
    x = np.array([[1.0], [4.0]])
    r = min_max_transform(x, is_cost=[True])
    assert r[0, 0] == pytest.approx(1.0)
    assert r[1, 0] == pytest.approx(0.0)


def test_min_max_constant_column_all_ones() -> None:
    x = np.ones((3, 1))
    r = min_max_transform(x, is_cost=[False])
    assert np.all(r == 1.0)


def test_topsis_explicit_two_alternatives() -> None:
    """
    After min–max and w=[0.5,0.5], both alternatives are symmetric ⇒ closeness ties.
    """
    x = np.array([[10.0, 2.0], [4.0, 5.0]])
    out = run_topsis(x, weights=[0.5, 0.5], is_cost=[False, False])
    assert out.closeness[0] == pytest.approx(0.5)
    assert out.closeness[1] == pytest.approx(0.5)


def test_topsis_prefers_high_skill_when_learning_equal() -> None:
    """Three jobs: purely benefit criteria; dominant first column ranks first."""
    x = np.array(
        [
            [0.2, 50_000, 1, 0],
            [0.9, 50_000, 1, 0],
            [0.5, 50_000, 1, 0],
        ]
    )
    w = np.array([0.5, 0.25, 0.2, 0.05])
    out = run_topsis(x, weights=w, is_cost=[False, False, False, True])
    assert out.ranked_indices[0] == 1


def test_topsis_learning_effort_is_cost() -> None:
    """Same match/salary/demand; lower learning effort must rank higher."""
    x = np.array(
        [
            [0.8, 60_000, 2, 5],
            [0.8, 60_000, 2, 1],
        ]
    )
    w = np.array([0.25, 0.25, 0.25, 0.25])
    out = run_topsis(x, weights=w, is_cost=[False, False, False, True])
    assert out.ranked_indices[0] == 1


def test_topsis_single_alternative() -> None:
    x = np.array([[0.5, 100.0, 2.0, 3.0]])
    w = np.ones(4) / 4
    out = run_topsis(x, weights=w, is_cost=[False, False, False, True])
    assert out.closeness.shape == (1,)
    assert out.ranked_indices.tolist() == [0]


def test_topsis_weights_mismatch_raises() -> None:
    x = np.array([[1.0, 2.0], [3.0, 4.0]])
    with pytest.raises(ValueError, match="weights length"):
        run_topsis(x, weights=[1.0], is_cost=[False, False])
