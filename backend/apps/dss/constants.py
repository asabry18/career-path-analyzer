"""Centralized DSS constants — no Django imports."""

from numbers import Real
from typing import Literal, Mapping

# Keys for pairwise / decision matrix criteria (plan Part B).
CRITERIA_KEYS: tuple[str, ...] = (
    "skill_match",
    "salary",
    "demand",
    "learning_effort",
)

LEVEL_BEGINNER = 0.2
LEVEL_UNDER_AVERAGE = 0.4
LEVEL_AVERAGE = 0.6
LEVEL_ABOVE_AVERAGE = 0.8
LEVEL_ADVANCED = 1.0
LEVEL_UNSPECIFIED = 0.0

SkillLevelLiteral = Literal[
    "beginner",
    "under average",
    "average",
    "above average",
    "advanced",
]

_SKILL_LEVEL_WEIGHTS: Mapping[str, float] = {
    "beginner": LEVEL_BEGINNER,
    "under average": LEVEL_UNDER_AVERAGE,
    "average": LEVEL_AVERAGE,
    "above average": LEVEL_ABOVE_AVERAGE,
    "advanced": LEVEL_ADVANCED,
    "advance": LEVEL_ADVANCED,
    "intermediate": LEVEL_AVERAGE,
}


def weight_from_skill_level(level: str | SkillLevelLiteral) -> float:
    """Map a named level string to its catalog weight."""
    key = level.strip().lower().replace("_", " ").replace("-", " ")
    key = " ".join(key.split())
    try:
        return float(_SKILL_LEVEL_WEIGHTS[key])
    except KeyError as exc:
        raise ValueError(f"Unknown skill level: {level!r}") from exc


def validate_unit_weight(weight: float) -> float:
    """Validate and return a frontend-provided numeric weight in [0, 1]."""
    w = float(weight)
    if w < 0.0 or w > 1.0:
        raise ValueError(f"Skill weight must be in [0, 1]; got {w!r}")
    return w


def skill_weights_from_levels(
    items: Mapping[int, float | SkillLevelLiteral | str],
) -> dict[int, float]:
    """
    Build primitive_id -> weight. Values may be floats in [0,1] or level names.

    ints are skill IDs only for typing clarity at call sites — no DB here.
    """
    out: dict[int, float] = {}
    for skill_id, value in items.items():
        sid = int(skill_id)
        if isinstance(value, Real) and not isinstance(value, bool):
            out[sid] = validate_unit_weight(float(value))
        else:
            out[sid] = weight_from_skill_level(str(value))
    return out
