"""TOPSIS multi-criteria ranking after column-wise min–max and AHP weights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from apps.dss.constants import CRITERIA_KEYS


@dataclass(frozen=True, slots=True)
class TopsisResult:
    """Per-alternative closeness to ideal (higher is better) and descending sort order."""

    closeness: np.ndarray
    ranked_indices: np.ndarray
    weighted_matrix: np.ndarray
    positive_ideal: np.ndarray
    negative_ideal: np.ndarray


def min_max_transform(
    matrix: np.ndarray,
    is_cost: Sequence[bool],
) -> np.ndarray:
    """
    Column-wise min–max to [0, 1]. Benefit columns: larger is better.
    Cost columns: smaller raw values become larger after transform.
    """
    x = np.asarray(matrix, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("decision matrix must be 2-D")
    n_rows, n_cols = x.shape
    if len(is_cost) != n_cols:
        raise ValueError("is_cost length must match number of columns")
    out = np.empty_like(x)
    for j in range(n_cols):
        col = x[:, j]
        cmin = float(np.min(col))
        cmax = float(np.max(col))
        if cmax > cmin:
            if is_cost[j]:
                out[:, j] = (cmax - col) / (cmax - cmin)
            else:
                out[:, j] = (col - cmin) / (cmax - cmin)
        else:
            out[:, j] = 1.0
    return out


def run_topsis(
    decision_matrix: np.ndarray,
    weights: np.ndarray | Sequence[float],
    is_cost: Sequence[bool] | None = None,
) -> TopsisResult:
    """
    Weighted TOPSIS on ``decision_matrix`` (rows = alternatives, columns = criteria).

    ``weights`` must be positive and are applied column-wise after min–max.
    Default ``is_cost``: only ``learning_effort`` is cost if columns match ``CRITERIA_KEYS`` order.
    """
    x = np.asarray(decision_matrix, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("decision matrix must be 2-D")
    n_rows, n_cols = x.shape
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if w.shape[0] != n_cols:
        raise ValueError("weights length must match number of columns")
    if np.any(w < 0) or float(w.sum()) == 0.0:
        raise ValueError("weights must be non-negative and sum to a positive value")

    if is_cost is None:
        if n_cols == len(CRITERIA_KEYS):
            is_cost = tuple(k == "learning_effort" for k in CRITERIA_KEYS)
        else:
            raise ValueError("is_cost is required when column count != len(CRITERIA_KEYS)")

    r = min_max_transform(x, is_cost)
    v = r * w[np.newaxis, :]

    positive_ideal = np.max(v, axis=0)
    negative_ideal = np.min(v, axis=0)

    dist_pos = np.sqrt(np.sum((v - positive_ideal) ** 2, axis=1))
    dist_neg = np.sqrt(np.sum((v - negative_ideal) ** 2, axis=1))
    denom = dist_pos + dist_neg
    with np.errstate(divide="ignore", invalid="ignore"):
        closeness = np.where(denom > 0, dist_neg / denom, 0.5)

    ranked_indices = np.argsort(-closeness)

    return TopsisResult(
        closeness=closeness,
        ranked_indices=ranked_indices,
        weighted_matrix=v,
        positive_ideal=positive_ideal,
        negative_ideal=negative_ideal,
    )
