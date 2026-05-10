"""
Integration tests for the full DSS pipeline (pipeline.py).

Uses the same frontend-user scenario from the hand-worked walkthrough:
  User: HTML=0.6, CSS=0.6, JS=0.9, React=0.9
  5 jobs from the real catalog, preference: demand >> learning_effort >> skill_match >> salary

Verifies the complete flow including Set Cover for the learning plan.
"""

import pytest

from apps.dss.ahp import PairwiseEntry
from apps.dss.pipeline import JobCatalogEntry, PipelineResult, run
from apps.dss.setcover import CourseInfo
from apps.dss.types import JobRequirements


# --- Skill IDs (same mapping used in the scenario walkthrough) ---
HTML = 1
CSS = 2
JS = 3
REACT = 4
ANGULAR = 5
VUE = 6
RESPONSIVE = 7
GIT = 8
API_INTEG = 9
UIUX = 10
BOOTSTRAP = 11
DATABASE = 12
SQL = 13
NOSQL = 14
DOCKER = 15
AWS = 16
RESTFUL = 17
UNIT_TEST = 18
NODEJS = 19
WORDPRESS = 20
PHP = 21
PLUGINS = 22
THEMES = 23
MYSQL = 24
PYTHON = 25
JAVA = 26
CSHARP = 27
REST_APIS = 28
MICROSERVICES = 29
SECURITY = 30
DJANGO_SK = 31
LARAVEL = 32
SPRING_BOOT = 33
FIGMA = 34
SKETCH = 35


def _demand_pairwise() -> list[PairwiseEntry]:
    """Demand most important, salary least."""
    return [
        PairwiseEntry("skill_match", "salary", 3),
        PairwiseEntry("skill_match", "demand", 1.0 / 5),
        PairwiseEntry("skill_match", "learning_effort", 1.0 / 3),
        PairwiseEntry("salary", "demand", 1.0 / 7),
        PairwiseEntry("salary", "learning_effort", 1.0 / 5),
        PairwiseEntry("demand", "learning_effort", 3),
    ]


@pytest.fixture
def catalog_jobs() -> list[JobCatalogEntry]:
    return [
        JobCatalogEntry(
            job_id=1, title="Frontend Developer",
            requirements=JobRequirements(
                1,
                frozenset({HTML, CSS, JS, RESPONSIVE, GIT, API_INTEG, UIUX, BOOTSTRAP}),
                (frozenset({REACT, ANGULAR, VUE}),),
            ),
            avg_salary=13.5, demand_score=47,
        ),
        JobCatalogEntry(
            job_id=2, title="Full Stack Developer",
            requirements=JobRequirements(
                2,
                frozenset({HTML, CSS, JS, DATABASE, SQL, NOSQL, GIT, DOCKER, AWS, RESTFUL, UNIT_TEST}),
                tuple(),
            ),
            avg_salary=16.5, demand_score=68,
        ),
        JobCatalogEntry(
            job_id=3, title="JavaScript Developer",
            requirements=JobRequirements(
                3,
                frozenset({JS, NODEJS, REACT, VUE, ANGULAR, GIT, HTML, CSS}),
                tuple(),
            ),
            avg_salary=18.0, demand_score=1,
        ),
        JobCatalogEntry(
            job_id=4, title="WordPress Developer",
            requirements=JobRequirements(
                4,
                frozenset({WORDPRESS, PHP, HTML, CSS, JS, PLUGINS, THEMES, MYSQL}),
                tuple(),
            ),
            avg_salary=16.5, demand_score=6,
        ),
        JobCatalogEntry(
            job_id=5, title="Backend Developer",
            requirements=JobRequirements(
                5,
                frozenset({PYTHON, JAVA, CSHARP, REST_APIS, DATABASE, SQL,
                           DOCKER, GIT, AWS, MICROSERVICES, SECURITY}),
                (frozenset({NODEJS, DJANGO_SK, LARAVEL, SPRING_BOOT}),),
            ),
            avg_salary=14.5, demand_score=90,
        ),
    ]


@pytest.fixture
def user_weights() -> dict[int, float]:
    return {HTML: 0.6, CSS: 0.6, JS: 0.9, REACT: 0.9}


@pytest.fixture
def courses() -> list[CourseInfo]:
    """Miniature course catalog covering some of the missing skills."""
    return [
        CourseInfo(101, "Git Intro", "Udemy", "https://example.com/git",
                   frozenset({GIT})),
        CourseInfo(102, "Responsive Design", "Coursera", "https://example.com/resp",
                   frozenset({RESPONSIVE})),
        CourseInfo(103, "Bootstrap+UI/UX", "Udemy", "https://example.com/bsux",
                   frozenset({BOOTSTRAP, UIUX})),
        CourseInfo(104, "API Integration", "Udemy", "https://example.com/api",
                   frozenset({API_INTEG})),
        CourseInfo(105, "Full Stack Foundations", "Coursera", "https://example.com/fs",
                   frozenset({DATABASE, SQL, NOSQL, DOCKER, AWS, RESTFUL, UNIT_TEST})),
        CourseInfo(106, "Node.js Intro", "Udemy", "https://example.com/node",
                   frozenset({NODEJS})),
        CourseInfo(107, "Vue+Angular Combo", "Udemy", "https://example.com/vueang",
                   frozenset({VUE, ANGULAR})),
        CourseInfo(108, "WordPress Dev", "Udemy", "https://example.com/wp",
                   frozenset({WORDPRESS, PHP, PLUGINS, THEMES, MYSQL})),
    ]


class TestPipelineIntegration:

    def test_full_pipeline_produces_valid_result(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        assert isinstance(result, PipelineResult)
        assert result.jobs_evaluated == 5
        assert result.jobs_after_threshold == 4
        assert len(result.ranked_jobs) == 4
        assert result.topsis is not None

    def test_backend_dev_filtered_out(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        ranked_ids = {rj.job_id for rj in result.ranked_jobs}
        assert 5 not in ranked_ids, "Backend Dev has 0 overlap, should be filtered"

    def test_ahp_weights_reflect_demand_priority(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        w = result.ahp.weights
        assert w["demand"] > w["learning_effort"] > w["skill_match"] > w["salary"]
        assert result.ahp.consistency_ratio < 0.1

    def test_topsis_ranking_order(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        ranked = result.ranked_jobs
        top2 = {ranked[0].job_id, ranked[1].job_id}
        assert top2 == {1, 2}, "Frontend + Full Stack should be top 2 with demand priority"

        for i in range(len(ranked) - 1):
            assert ranked[i].topsis_score >= ranked[i + 1].topsis_score

    def test_learning_effort_values(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        effort = {rj.job_id: rj.learning_effort for rj in result.ranked_jobs}
        assert effort[1] == 5   # Frontend: 5 missing mandatory, slot covered by React
        assert effort[2] == 8   # Full Stack: 8 missing
        assert effort[3] == 4   # JS Dev: 4 missing
        assert effort[4] == 5   # WordPress: 5 missing

    def test_missing_skills_for_frontend(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        frontend = next(rj for rj in result.ranked_jobs if rj.job_id == 1)
        expected_missing = {RESPONSIVE, GIT, API_INTEG, UIUX, BOOTSTRAP}
        assert set(frontend.missing_mandatory_skill_ids) == expected_missing
        assert frontend.optional_framework_gaps == [], \
            "User knows React, so the OR slot is satisfied"

    def test_optional_frameworks_for_fullstack(self, catalog_jobs, user_weights, courses):
        """Full Stack has no OR slot → no framework gaps."""
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        fullstack = next(rj for rj in result.ranked_jobs if rj.job_id == 2)
        assert fullstack.optional_framework_gaps == []

    def test_set_cover_produces_learning_plan(self, catalog_jobs, user_weights, courses):
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        sc = result.set_cover
        assert sc.solver_status == "Optimal"
        assert len(sc.selected_courses) > 0
        assert len(sc.covered_skill_ids) > 0

    def test_set_cover_covers_mandatory_gaps(self, catalog_jobs, user_weights, courses):
        """GIT is missing for multiple jobs and course 101 teaches it → must be covered."""
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=courses,
        )
        assert GIT in result.set_cover.covered_skill_ids

    def test_pipeline_with_no_courses(self, catalog_jobs, user_weights):
        """Pipeline works even when no courses are provided (empty learning plan)."""
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.1,
            courses=[],
        )
        assert result.set_cover.selected_courses == []
        assert len(result.set_cover.uncovered_skill_ids) > 0
        assert len(result.ranked_jobs) == 4

    def test_pipeline_threshold_zero(self, catalog_jobs, user_weights, courses):
        """Threshold 0 keeps all 5 jobs including Backend Dev (score=0)."""
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.0,
            courses=courses,
        )
        assert result.jobs_after_threshold == 5
        assert len(result.ranked_jobs) == 5

    def test_pipeline_no_candidates(self, catalog_jobs, user_weights, courses):
        """Very high threshold → no candidates → empty result with valid structure."""
        result = run(
            jobs=catalog_jobs,
            user_weights=user_weights,
            pairwise=_demand_pairwise(),
            threshold=0.99,
            courses=courses,
        )
        assert result.ranked_jobs == []
        assert result.topsis is None
        assert result.jobs_after_threshold == 0
