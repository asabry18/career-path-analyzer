"""Set Cover via PuLP — minimum courses to cover a set of missing skills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import pulp


@dataclass(frozen=True, slots=True)
class CourseInfo:
    """Lightweight course descriptor (no Django imports)."""

    course_id: int
    title: str
    provider: str
    url: str
    skill_ids: frozenset[int]


@dataclass(frozen=True, slots=True)
class SetCoverResult:
    """Outcome of the ILP solver."""

    selected_courses: list[CourseInfo]
    covered_skill_ids: frozenset[int]
    uncovered_skill_ids: frozenset[int]
    solver_status: str


def solve_set_cover(
    missing_skill_ids: frozenset[int] | set[int],
    available_courses: Sequence[CourseInfo],
) -> SetCoverResult:
    """
    Minimize the number of courses selected such that every skill in
    ``missing_skill_ids`` is taught by at least one chosen course.

    Courses that teach no missing skill are ignored. If a skill cannot be
    covered by any available course it is reported in ``uncovered_skill_ids``.
    """
    target = frozenset(missing_skill_ids)
    if not target:
        return SetCoverResult(
            selected_courses=[],
            covered_skill_ids=frozenset(),
            uncovered_skill_ids=frozenset(),
            solver_status="Optimal",
        )

    relevant: list[CourseInfo] = []
    for c in available_courses:
        if c.skill_ids & target:
            relevant.append(c)

    coverable: set[int] = set()
    for c in relevant:
        coverable |= (c.skill_ids & target)
    uncoverable = target - coverable

    skills_to_cover = target & coverable
    if not skills_to_cover:
        return SetCoverResult(
            selected_courses=[],
            covered_skill_ids=frozenset(),
            uncovered_skill_ids=target,
            solver_status="Optimal",
        )

    prob = pulp.LpProblem("SetCover", pulp.LpMinimize)

    x = {
        c.course_id: pulp.LpVariable(f"x_{c.course_id}", cat=pulp.LpBinary)
        for c in relevant
    }

    prob += pulp.lpSum(x.values()), "MinCourses"

    for sid in skills_to_cover:
        teaching = [
            x[c.course_id] for c in relevant if sid in c.skill_ids
        ]
        if teaching:
            prob += pulp.lpSum(teaching) >= 1, f"cover_skill_{sid}"

    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[prob.status]

    selected: list[CourseInfo] = []
    if status == "Optimal":
        for c in relevant:
            if pulp.value(x[c.course_id]) and pulp.value(x[c.course_id]) > 0.5:
                selected.append(c)

    actually_covered: set[int] = set()
    for c in selected:
        actually_covered |= (c.skill_ids & target)

    return SetCoverResult(
        selected_courses=selected,
        covered_skill_ids=frozenset(actually_covered),
        uncovered_skill_ids=target - actually_covered,
        solver_status=status,
    )
