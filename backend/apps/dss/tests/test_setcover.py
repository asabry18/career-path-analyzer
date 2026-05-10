"""Unit tests for Set Cover ILP solver."""

import pytest

from apps.dss.setcover import CourseInfo, solve_set_cover


def _course(cid: int, title: str, skill_ids: set[int]) -> CourseInfo:
    return CourseInfo(
        course_id=cid,
        title=title,
        provider="TestPlatform",
        url=f"https://example.com/course/{cid}",
        skill_ids=frozenset(skill_ids),
    )


class TestSetCover:

    def test_empty_missing_returns_nothing(self):
        result = solve_set_cover(frozenset(), [_course(1, "C1", {1, 2})])
        assert result.selected_courses == []
        assert result.solver_status == "Optimal"

    def test_single_course_covers_all(self):
        courses = [_course(1, "Fullstack 101", {1, 2, 3})]
        result = solve_set_cover({1, 2, 3}, courses)
        assert len(result.selected_courses) == 1
        assert result.selected_courses[0].course_id == 1
        assert result.covered_skill_ids == frozenset({1, 2, 3})
        assert result.uncovered_skill_ids == frozenset()

    def test_picks_minimum_courses(self):
        """Two skills, one course covers both, two courses cover one each → pick the one."""
        courses = [
            _course(1, "Only A", {10}),
            _course(2, "Only B", {20}),
            _course(3, "Both A+B", {10, 20}),
        ]
        result = solve_set_cover({10, 20}, courses)
        assert len(result.selected_courses) == 1
        assert result.selected_courses[0].course_id == 3

    def test_needs_two_courses_when_no_single_covers_all(self):
        courses = [
            _course(1, "Python basics", {1}),
            _course(2, "SQL basics", {2}),
            _course(3, "Git intro", {3}),
        ]
        result = solve_set_cover({1, 2}, courses)
        assert len(result.selected_courses) == 2
        selected_ids = {c.course_id for c in result.selected_courses}
        assert selected_ids == {1, 2}
        assert result.covered_skill_ids == frozenset({1, 2})

    def test_uncoverable_skill_reported(self):
        """Skill 99 has no matching course → appears in uncovered."""
        courses = [_course(1, "Python", {1})]
        result = solve_set_cover({1, 99}, courses)
        assert 99 in result.uncovered_skill_ids
        assert 1 in result.covered_skill_ids
        assert len(result.selected_courses) == 1

    def test_no_courses_available(self):
        result = solve_set_cover({1, 2, 3}, [])
        assert result.selected_courses == []
        assert result.uncovered_skill_ids == frozenset({1, 2, 3})

    def test_overlapping_courses_picks_optimal(self):
        """
        Missing: {1,2,3,4}
        Course A covers {1,2,3}, Course B covers {3,4}, Course C covers {1}.
        Optimal: A + B (2 courses).
        """
        courses = [
            _course(1, "A", {1, 2, 3}),
            _course(2, "B", {3, 4}),
            _course(3, "C", {1}),
        ]
        result = solve_set_cover({1, 2, 3, 4}, courses)
        assert len(result.selected_courses) == 2
        selected_ids = {c.course_id for c in result.selected_courses}
        assert selected_ids == {1, 2}
        assert result.uncovered_skill_ids == frozenset()

    def test_irrelevant_courses_ignored(self):
        """Courses that teach none of the missing skills are not selected."""
        courses = [
            _course(1, "Relevant", {5}),
            _course(2, "Irrelevant", {99, 100}),
        ]
        result = solve_set_cover({5}, courses)
        assert len(result.selected_courses) == 1
        assert result.selected_courses[0].course_id == 1
