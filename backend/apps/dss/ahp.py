"""Analytic Hierarchy Process — pairwise comparisons → weights and consistency ratio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from apps.dss.constants import CRITERIA_KEYS

# Random index for consistency ratio (Saaty). n=1,2: undefined; use 0 for CR denominator.
_RI: dict[int, float] = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


@dataclass(frozen=True, slots=True)
class PairwiseEntry:
    """One directed comparison: criterion ``a`` vs ``b`` with Saaty intensity ``value``."""

    a: str
    b: str
    value: float


@dataclass(frozen=True, slots=True)
class AhpResult:
    """Normalized AHP weights, principal eigenvalue, and consistency ratio."""

    weights: dict[str, float]
    lambda_max: float
    consistency_ratio: float


def ri_for_n(n: int) -> float:
    """Random index for ``n`` criteria; extended with a rough tail for n > 10."""
    if n <= 0:
        return 0.0
    if n in _RI:
        return _RI[n]
    return 1.49 + 0.04 * (n - 10)


def build_pairwise_matrix(
    entries: Sequence[PairwiseEntry | Mapping[str, object]],
    criteria_order: Sequence[str] | None = None,
) -> np.ndarray:
    """
    Build a positive reciprocal comparison matrix from exactly one entry per unordered pair.

    ``value`` means: ``a`` is ``value`` times as important as ``b`` (Saaty scale, typically 1–9).
    """
    order = tuple(criteria_order) if criteria_order is not None else CRITERIA_KEYS
    n = len(order)
    if n == 0:
        raise ValueError("criteria_order must be non-empty")
    unknown = set(order) - set(CRITERIA_KEYS)
    if unknown:
        raise ValueError(f"Unknown criteria keys: {sorted(unknown)}")

    idx: dict[str, int] = {k: i for i, k in enumerate(order)}
    mat = np.ones((n, n), dtype=np.float64)
    seen_pairs: set[tuple[int, int]] = set()

    for raw in entries:
        e = (
            raw
            if isinstance(raw, PairwiseEntry)
            else PairwiseEntry(
                a=str(raw["a"]),
                b=str(raw["b"]),
                value=float(raw["value"]),
            )
        )
        if e.a not in idx or e.b not in idx:
            raise ValueError(f"Unknown criterion in pairwise entry: {e.a!r}, {e.b!r}")
        i, j = idx[e.a], idx[e.b]
        if i == j:
            raise ValueError("Pairwise entry cannot compare a criterion to itself")
        key = (min(i, j), max(i, j))
        if key in seen_pairs:
            raise ValueError(f"Duplicate comparison for pair {order[key[0]]!r}, {order[key[1]]!r}")
        seen_pairs.add(key)
        v = float(e.value)
        if v <= 0:
            raise ValueError(f"Pairwise value must be positive; got {v!r}")
        mat[i, j] = v
        mat[j, i] = 1.0 / v

    expected_pairs = n * (n - 1) // 2
    if len(seen_pairs) != expected_pairs:
        raise ValueError(
            f"Expected {expected_pairs} unique unordered pairwise comparisons for n={n}, "
            f"got {len(seen_pairs)}"
        )
    return mat


def assert_reciprocal(mat: np.ndarray, tolerance: float = 1e-8) -> None:
    """Verify ``mat[i,j] * mat[j,i] ≈ 1`` for off-diagonal entries."""
    n = mat.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            prod = float(mat[i, j] * mat[j, i])
            if abs(prod - 1.0) > tolerance:
                raise ValueError(f"Matrix not reciprocal at ({i},{j}): product={prod}")


def principal_eigenvector_weights(mat: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Dominant eigenpair of ``mat``. Weights are the real eigenvector normalized to sum 1.
    """
    n = mat.shape[0]
    if n == 0:
        raise ValueError("Empty matrix")
    eigvals, eigvecs = np.linalg.eig(mat)
    real_parts = np.real(eigvals)
    idx = int(np.argmax(real_parts))
    lambda_max = float(np.real(eigvals[idx]))
    w = np.real(eigvecs[:, idx])
    w = np.abs(w)
    s = float(w.sum())
    if s == 0.0:
        raise ValueError("Principal eigenvector has zero sum")
    w = w / s
    return w, lambda_max


def consistency_ratio(lambda_max: float, n: int) -> float:
    """CR = CI / RI, with CI = (λ_max - n) / (n - 1). For n < 3, CR is 0."""
    if n < 3:
        return 0.0
    ci = (lambda_max - n) / (n - 1)
    ri = ri_for_n(n)
    if ri <= 0.0:
        return 0.0
    return float(ci / ri)


def run_ahp(
    entries: Sequence[PairwiseEntry | Mapping[str, object]],
    criteria_order: Sequence[str] | None = None,
) -> AhpResult:
    """
    Full AHP: build matrix, principal eigenvector weights, λ_max, consistency ratio.
    """
    order = tuple(criteria_order) if criteria_order is not None else CRITERIA_KEYS
    mat = build_pairwise_matrix(entries, order)
    assert_reciprocal(mat)
    w, lambda_max = principal_eigenvector_weights(mat)
    cr = consistency_ratio(lambda_max, len(order))
    weights = {order[i]: float(w[i]) for i in range(len(order))}
    return AhpResult(weights=weights, lambda_max=lambda_max, consistency_ratio=cr)


_RANK_GAP_TO_INTENSITY: dict[int, float] = {
    0: 3.0,
    1: 5.0,
    2: 7.0,
}


def pairwise_from_priority_ranking(
    ranked_criteria: Sequence[str],
) -> list[PairwiseEntry]:
    """
    Convert an ordered priority list (index 0 = most important) into Saaty
    pairwise entries.

    Gap mapping (positions between two criteria in the ranking):
        adjacent (gap 0) → 3,  one apart (gap 1) → 5,  two apart (gap 2) → 7.

    This matches the user-facing rule:
        rank 1 vs rank 2 = 3, vs rank 3 = 5, vs rank 4 = 7
        rank 2 vs rank 3 = 3, vs rank 4 = 5
        rank 3 vs rank 4 = 3
    """
    n = len(ranked_criteria)
    entries: list[PairwiseEntry] = []
    for i in range(n):
        for j in range(i + 1, n):
            gap = j - i - 1
            intensity = _RANK_GAP_TO_INTENSITY.get(gap, 7.0 + 2.0 * (gap - 3))
            entries.append(PairwiseEntry(
                a=ranked_criteria[i],
                b=ranked_criteria[j],
                value=intensity,
            ))
    return entries


def run_ahp_from_matrix(mat: np.ndarray, criteria_order: Sequence[str] | None = None) -> AhpResult:
    """Same as ``run_ahp`` but from an existing positive reciprocal matrix."""
    order = tuple(criteria_order) if criteria_order is not None else CRITERIA_KEYS
    if mat.shape != (len(order), len(order)):
        raise ValueError("Matrix shape must match criteria_order length")
    assert_reciprocal(mat)
    w, lambda_max = principal_eigenvector_weights(mat)
    cr = consistency_ratio(lambda_max, len(order))
    weights = {order[i]: float(w[i]) for i in range(len(order))}
    return AhpResult(weights=weights, lambda_max=lambda_max, consistency_ratio=cr)
