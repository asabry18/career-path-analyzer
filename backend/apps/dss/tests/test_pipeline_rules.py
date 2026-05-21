"""
Rule-based test suite covering the full DSS pipeline through Step 7.

Rules are grouped:
  S  — Similarity (cosine on shared vocab)
  T  — Threshold filtering
  L  — Learning effort calculation
  A  — AHP pairwise weights + consistency
  TP — TOPSIS ranking
  E  — End-to-end mini-pipeline (similarity → threshold → AHP → TOPSIS)

Each test is named after its rule ID for traceability.
"""

import math

import numpy as np
import pytest

from apps.dss.ahp import PairwiseEntry, run_ahp
from apps.dss.constants import CRITERIA_KEYS
from apps.dss.similarity import (
    build_vocab_skill_ids_ordered,
    skill_match_breakdown,
    skill_match_score,
)
from apps.dss.topsis import run_topsis
from apps.dss.types import JobRequirements


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vocab(*jobs: JobRequirements, user: dict[int, float]) -> tuple[int, ...]:
    return build_vocab_skill_ids_ordered(jobs, user)


def _six_equal_pairs() -> list[PairwiseEntry]:
    """All criteria equally important."""
    keys = list(CRITERIA_KEYS)
    return [
        PairwiseEntry(keys[i], keys[j], 1.0)
        for i in range(len(keys))
        for j in range(i + 1, len(keys))
    ]


def _plan_pairwise() -> list[PairwiseEntry]:
    """The Part D example: skill_match strongly preferred."""
    return [
        PairwiseEntry("skill_match", "salary", 3),
        PairwiseEntry("skill_match", "demand", 5),
        PairwiseEntry("skill_match", "learning_effort", 7),
        PairwiseEntry("salary", "demand", 3),
        PairwiseEntry("salary", "learning_effort", 5),
        PairwiseEntry("demand", "learning_effort", 3),
    ]


def _learning_effort(
    job: JobRequirements,
    user_weights: dict[int, float],
) -> int:
    """Compute learning effort the same way debug_views does (pure Python)."""
    missing_mandatory = sum(
        1 for sid in job.mandatory_skill_ids
        if user_weights.get(sid, 0.0) <= 0.0
    )
    unmatched_slots = 0
    for slot in job.framework_slots:
        mx = max((user_weights.get(sid, 0.0) for sid in slot), default=0.0)
        if mx <= 0.0:
            unmatched_slots += 1
    return missing_mandatory + unmatched_slots


def _mini_pipeline(
    jobs_data: list[dict],
    user_weights: dict[int, float],
    pairwise: list[PairwiseEntry],
    threshold: float = 0.0,
) -> dict:
    """
    Reproduce the debug_views pipeline in pure DSS code (no Django).

    Each ``jobs_data`` item: {"job": JobRequirements, "salary": float, "demand": int}
    Returns {"ahp": AhpResult, "candidates": [...], "ranked": [...], "topsis": TopsisResult|None}
    """
    job_reqs = [d["job"] for d in jobs_data]
    vocab = build_vocab_skill_ids_ordered(job_reqs, user_weights)

    candidates = []
    for d in jobs_data:
        jr = d["job"]
        sc = skill_match_score(jr, user_weights, vocab_skill_ids_ordered=vocab)
        if sc < threshold:
            continue
        le = _learning_effort(jr, user_weights)
        candidates.append({
            "job_id": jr.job_id,
            "skill_match": sc,
            "salary": float(d["salary"]),
            "demand": int(d["demand"]),
            "learning_effort": le,
        })

    ahp = run_ahp(pairwise)

    if not candidates:
        return {"ahp": ahp, "candidates": candidates, "ranked": [], "topsis": None}

    matrix = np.array([
        [c["skill_match"], c["salary"], c["demand"], c["learning_effort"]]
        for c in candidates
    ])
    w_vec = np.array([ahp.weights[k] for k in CRITERIA_KEYS])
    topsis = run_topsis(matrix, w_vec, is_cost=[False, False, False, True])

    ranked = []
    for rank, idx in enumerate(topsis.ranked_indices.tolist(), start=1):
        c = candidates[idx]
        ranked.append({
            **c,
            "rank": rank,
            "topsis_score": float(topsis.closeness[idx]),
        })

    return {"ahp": ahp, "candidates": candidates, "ranked": ranked, "topsis": topsis}


# ===================================================================
# Rule Group S — Similarity
# ===================================================================

class TestSimilarityRules:

    def test_s1_perfect_match_score_1(self):
        """User has exactly the job's skills at weight 1.0, no extras → score = 1.0."""
        job = JobRequirements(1, frozenset({1, 2, 3}), tuple())
        user = {1: 1.0, 2: 1.0, 3: 1.0}
        vocab = _vocab(job, user=user)
        assert skill_match_score(job, user, vocab_skill_ids_ordered=vocab) == pytest.approx(1.0)

    def test_s2_no_overlap_score_0(self):
        """User skills are completely disjoint from job skills → score = 0.0."""
        job = JobRequirements(1, frozenset({1, 2}), tuple())
        user = {10: 0.9, 11: 0.8}
        vocab = _vocab(job, user=user)
        assert skill_match_score(job, user, vocab_skill_ids_ordered=vocab) == pytest.approx(0.0)

    def test_s3_higher_weights_higher_score(self):
        """Same skill set, higher weights → higher cosine score."""
        job = JobRequirements(1, frozenset({1, 2}), tuple())
        user_low = {1: 0.3, 2: 0.3}
        user_high = {1: 0.9, 2: 0.9}
        vocab_low = _vocab(job, user=user_low)
        vocab_high = _vocab(job, user=user_high)
        s_low = skill_match_score(job, user_low, vocab_skill_ids_ordered=vocab_low)
        s_high = skill_match_score(job, user_high, vocab_skill_ids_ordered=vocab_high)
        # With only job skills in vocab, both are perfect matches (cos=1 regardless of weight magnitude)
        # So we need extra user skills to see differentiation. Add an extra skill.
        user_low_extra = {1: 0.3, 2: 0.3, 99: 0.5}
        user_high_extra = {1: 0.9, 2: 0.9, 99: 0.5}
        vocab2 = _vocab(job, user=user_low_extra)
        s_low2 = skill_match_score(job, user_low_extra, vocab_skill_ids_ordered=vocab2)
        s_high2 = skill_match_score(job, user_high_extra, vocab_skill_ids_ordered=vocab2)
        assert s_high2 > s_low2

    def test_s4_extra_user_skills_dilute_score(self):
        """Adding irrelevant user skills increases ‖u‖ without changing u·j → lower cosine."""
        job = JobRequirements(1, frozenset({1, 2}), tuple())
        user_focused = {1: 0.9, 2: 0.9}
        user_diluted = {1: 0.9, 2: 0.9, 50: 0.8, 51: 0.7}
        vocab_f = _vocab(job, user=user_focused)
        vocab_d = _vocab(job, user=user_diluted)
        s_focused = skill_match_score(job, user_focused, vocab_skill_ids_ordered=vocab_f)
        s_diluted = skill_match_score(job, user_diluted, vocab_skill_ids_ordered=vocab_d)
        assert s_focused > s_diluted

    def test_s5_framework_or_slot_single_alt_satisfied(self):
        """User knows 1 of 3 framework alternatives → slot contributes to match."""
        react, vue, angular = 101, 102, 103
        job = JobRequirements(
            1,
            frozenset({10}),  # mandatory: Python
            (frozenset({react, vue, angular}),),  # OR slot
        )
        user = {10: 0.9, vue: 0.6}  # knows Python + Vue only
        vocab = _vocab(job, user=user)
        bd = skill_match_breakdown(job, user, vocab_skill_ids_ordered=vocab)
        assert bd["score"] > 0.0
        assert bd["job_binary_skill_count"] == 4  # Python + React + Vue + Angular all set to 1


# ===================================================================
# Rule Group T — Threshold
# ===================================================================

class TestThresholdRules:

    def _make_scenario(self):
        """Two jobs: one with good match, one with bad match."""
        good_job = JobRequirements(1, frozenset({1, 2}), tuple())
        bad_job = JobRequirements(2, frozenset({10, 11, 12}), tuple())
        user = {1: 0.9, 2: 0.9}
        return [
            {"job": good_job, "salary": 50000, "demand": 5},
            {"job": bad_job, "salary": 80000, "demand": 8},
        ], user

    def test_t1_below_threshold_excluded(self):
        """Job with score below threshold is dropped."""
        jobs_data, user = self._make_scenario()
        result = _mini_pipeline(jobs_data, user, _six_equal_pairs(), threshold=0.5)
        surviving_ids = {c["job_id"] for c in result["candidates"]}
        assert 2 not in surviving_ids

    def test_t2_at_or_above_threshold_kept(self):
        """Job at or above threshold survives."""
        jobs_data, user = self._make_scenario()
        result = _mini_pipeline(jobs_data, user, _six_equal_pairs(), threshold=0.5)
        surviving_ids = {c["job_id"] for c in result["candidates"]}
        assert 1 in surviving_ids

    def test_t3_threshold_zero_keeps_everything(self):
        """Threshold 0.0 lets all jobs through (including zero-score ones)."""
        jobs_data, user = self._make_scenario()
        result = _mini_pipeline(jobs_data, user, _six_equal_pairs(), threshold=0.0)
        assert len(result["candidates"]) == 2


# ===================================================================
# Rule Group L — Learning Effort
# ===================================================================

class TestLearningEffortRules:

    def test_l1_missing_mandatory_adds_one_each(self):
        """Each mandatory skill the user lacks (weight ≤ 0) adds +1."""
        job = JobRequirements(1, frozenset({1, 2, 3}), tuple())
        user = {1: 0.9}  # has skill 1, missing 2 and 3
        assert _learning_effort(job, user) == 2

    def test_l2_unmatched_framework_slot_adds_one_not_n(self):
        """An OR slot where user knows none → +1 (not +3 for the 3 alternatives)."""
        job = JobRequirements(1, frozenset(), (frozenset({101, 102, 103}),))
        user = {999: 0.5}
        assert _learning_effort(job, user) == 1

    def test_l3_matched_framework_slot_adds_zero(self):
        """User knows at least one alternative in the slot → +0 effort."""
        job = JobRequirements(1, frozenset(), (frozenset({101, 102, 103}),))
        user = {102: 0.6}
        assert _learning_effort(job, user) == 0

    def test_l4_perfect_user_zero_effort(self):
        """User has every mandatory skill and every OR slot covered → effort = 0."""
        job = JobRequirements(
            1,
            frozenset({1, 2}),
            (frozenset({101, 102}), frozenset({201, 202})),
        )
        user = {1: 0.9, 2: 0.8, 101: 0.7, 201: 0.6}
        assert _learning_effort(job, user) == 0

    def test_l_combined_mandatory_and_slot_effort(self):
        """2 missing mandatory + 1 unmatched slot → effort = 3."""
        job = JobRequirements(
            1,
            frozenset({1, 2, 3}),
            (frozenset({101, 102}),),
        )
        user = {1: 0.5}  # has skill 1; missing 2,3; missing slot
        assert _learning_effort(job, user) == 3


# ===================================================================
# Rule Group A — AHP
# ===================================================================

class TestAhpRules:

    def test_a1_equal_importance_gives_equal_weights(self):
        res = run_ahp(_six_equal_pairs())
        for k in CRITERIA_KEYS:
            assert res.weights[k] == pytest.approx(0.25)

    def test_a2_weights_sum_to_one(self):
        res = run_ahp(_plan_pairwise())
        assert sum(res.weights.values()) == pytest.approx(1.0)

    def test_a3_higher_pairwise_gives_higher_weight(self):
        """Skill_match is preferred over everything in plan pairwise → highest weight."""
        res = run_ahp(_plan_pairwise())
        assert res.weights["skill_match"] == max(res.weights.values())
        assert res.weights["learning_effort"] == min(res.weights.values())

    def test_a4_perfectly_consistent_cr_zero(self):
        res = run_ahp(_six_equal_pairs())
        assert res.consistency_ratio == pytest.approx(0.0, abs=1e-6)

    def test_a5_invalid_pairwise_raises(self):
        with pytest.raises(ValueError, match="Expected 6"):
            run_ahp([PairwiseEntry("skill_match", "salary", 3)])
        with pytest.raises(ValueError, match="Duplicate"):
            run_ahp([
                PairwiseEntry("skill_match", "salary", 3),
                PairwiseEntry("salary", "skill_match", 2),
                PairwiseEntry("skill_match", "demand", 5),
                PairwiseEntry("skill_match", "learning_effort", 7),
                PairwiseEntry("salary", "demand", 3),
                PairwiseEntry("salary", "learning_effort", 5),
                PairwiseEntry("demand", "learning_effort", 3),
            ])
        with pytest.raises(ValueError, match="positive"):
            run_ahp([
                PairwiseEntry("skill_match", "salary", -1),
                PairwiseEntry("skill_match", "demand", 5),
                PairwiseEntry("skill_match", "learning_effort", 7),
                PairwiseEntry("salary", "demand", 3),
                PairwiseEntry("salary", "learning_effort", 5),
                PairwiseEntry("demand", "learning_effort", 3),
            ])


# ===================================================================
# Rule Group TP — TOPSIS
# ===================================================================

class TestTopsisRules:

    def test_tp1_dominant_alternative_ranks_first(self):
        """Job best in EVERY column → rank 1."""
        x = np.array([
            [0.9, 80000, 9, 0],  # best everywhere (lowest cost too)
            [0.5, 50000, 5, 3],
            [0.2, 30000, 2, 6],
        ])
        w = np.ones(4) / 4
        out = run_topsis(x, w, is_cost=[False, False, False, True])
        assert out.ranked_indices[0] == 0
        assert out.closeness[0] == pytest.approx(1.0)

    def test_tp2_lower_learning_effort_better(self):
        """Same benefits, less effort → higher closeness."""
        x = np.array([
            [0.7, 60000, 5, 5],
            [0.7, 60000, 5, 1],
        ])
        w = np.ones(4) / 4
        out = run_topsis(x, w, is_cost=[False, False, False, True])
        assert out.ranked_indices[0] == 1

    def test_tp3_single_alternative_closeness_half(self):
        """One row → all columns are constant → closeness = 0.5."""
        x = np.array([[0.8, 70000, 6, 2]])
        w = np.ones(4) / 4
        out = run_topsis(x, w, is_cost=[False, False, False, True])
        assert out.closeness[0] == pytest.approx(0.5)

    def test_tp4_ahp_weight_shift_changes_ranking(self):
        """
        Job A: high skill match, low salary.
        Job B: low skill match, high salary.
        Weighting skill_match more → A wins. Weighting salary more → B wins.
        """
        x = np.array([
            [0.95, 30000, 5, 2],  # A: great match, low pay
            [0.40, 90000, 5, 2],  # B: poor match, high pay
        ])
        w_skill = np.array([0.7, 0.1, 0.1, 0.1])
        w_salary = np.array([0.1, 0.7, 0.1, 0.1])
        r_skill = run_topsis(x, w_skill, is_cost=[False, False, False, True])
        r_salary = run_topsis(x, w_salary, is_cost=[False, False, False, True])
        assert r_skill.ranked_indices[0] == 0, "Skill-weighted: A should win"
        assert r_salary.ranked_indices[0] == 1, "Salary-weighted: B should win"


# ===================================================================
# Rule Group E — End-to-End Mini-Pipeline
# ===================================================================

class TestEndToEndPipeline:

    @pytest.fixture
    def three_job_scenario(self):
        """
        3 jobs with known characteristics:
          Job 1 (Data Analyst):  mandatory={Python, SQL, Excel}, salary=55k, demand=7
          Job 2 (Backend Dev):   mandatory={Python, SQL}, OR slot={Node.js, Django}, salary=75k, demand=8
          Job 3 (Designer):      mandatory={Figma, Sketch}, salary=45k, demand=4

        User: Python=0.9, SQL=0.6, Excel=0.3, Django=0.6
        """
        py, sql, excel, nodejs, django_sk, figma, sketch = 1, 2, 3, 4, 5, 6, 7

        jobs_data = [
            {
                "job": JobRequirements(1, frozenset({py, sql, excel}), tuple()),
                "salary": 55000,
                "demand": 7,
            },
            {
                "job": JobRequirements(
                    2,
                    frozenset({py, sql}),
                    (frozenset({nodejs, django_sk}),),
                ),
                "salary": 75000,
                "demand": 8,
            },
            {
                "job": JobRequirements(3, frozenset({figma, sketch}), tuple()),
                "salary": 45000,
                "demand": 4,
            },
        ]
        user_weights = {py: 0.9, sql: 0.6, excel: 0.3, django_sk: 0.6}
        return jobs_data, user_weights

    def test_e1_full_pipeline_produces_ranked_results(self, three_job_scenario):
        """Full flow produces ranked_jobs with correct fields."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise(), threshold=0.0)

        assert len(result["ranked"]) == 3
        assert sum(result["ahp"].weights.values()) == pytest.approx(1.0)
        for r in result["ranked"]:
            assert "rank" in r
            assert "topsis_score" in r
            assert 0.0 <= r["topsis_score"] <= 1.0

        ranks = [r["rank"] for r in result["ranked"]]
        assert ranks == [1, 2, 3]

    def test_e1_learning_effort_correct_per_job(self, three_job_scenario):
        """Verify learning effort for each job matches the rules."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise(), threshold=0.0)

        effort_map = {c["job_id"]: c["learning_effort"] for c in result["candidates"]}
        # Job 1: user has Python(0.9), SQL(0.6), Excel(0.3) → all > 0 → effort=0
        assert effort_map[1] == 0
        # Job 2: mandatory={Python,SQL} all present; OR slot={Node.js,Django} → user has Django(0.6)>0 → effort=0
        assert effort_map[2] == 0
        # Job 3: mandatory={Figma,Sketch} → user has neither → effort=2
        assert effort_map[3] == 2

    def test_e1_similarity_scores_ordered_sensibly(self, three_job_scenario):
        """Job 1 and 2 should score higher than Job 3 (no overlap for designer)."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise(), threshold=0.0)

        scores = {c["job_id"]: c["skill_match"] for c in result["candidates"]}
        assert scores[1] > scores[3]
        assert scores[2] > scores[3]
        assert scores[3] == pytest.approx(0.0)

    def test_e2_threshold_filters_midpipeline(self, three_job_scenario):
        """Threshold 0.3 should exclude Job 3 (score=0.0), keep Jobs 1 and 2."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise(), threshold=0.3)

        surviving_ids = {c["job_id"] for c in result["candidates"]}
        assert surviving_ids == {1, 2}
        assert len(result["ranked"]) == 2

    def test_e3_ahp_weight_shift_changes_winner(self, three_job_scenario):
        """
        With skill_match strongly preferred → Job 1 or 2 wins.
        With salary strongly preferred → Job 2 wins (highest salary among matched).
        """
        jobs_data, user = three_job_scenario

        skill_pairwise = [
            PairwiseEntry("skill_match", "salary", 9),
            PairwiseEntry("skill_match", "demand", 9),
            PairwiseEntry("skill_match", "learning_effort", 9),
            PairwiseEntry("salary", "demand", 1),
            PairwiseEntry("salary", "learning_effort", 1),
            PairwiseEntry("demand", "learning_effort", 1),
        ]
        salary_pairwise = [
            PairwiseEntry("skill_match", "salary", 1.0 / 9),
            PairwiseEntry("skill_match", "demand", 1),
            PairwiseEntry("skill_match", "learning_effort", 1),
            PairwiseEntry("salary", "demand", 9),
            PairwiseEntry("salary", "learning_effort", 9),
            PairwiseEntry("demand", "learning_effort", 1),
        ]

        r_skill = _mini_pipeline(jobs_data, user, skill_pairwise, threshold=0.1)
        r_salary = _mini_pipeline(jobs_data, user, salary_pairwise, threshold=0.1)

        top_skill = r_skill["ranked"][0]["job_id"]
        top_salary = r_salary["ranked"][0]["job_id"]

        assert top_skill in (1, 2), "Skill-weighted: a matched job should win"
        assert top_salary == 2, "Salary-weighted: Backend Dev (75k) should win"

    def test_e_consistency_ratio_below_threshold(self, three_job_scenario):
        """Plan pairwise from Part D should be consistent (CR < 0.1)."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise())
        assert result["ahp"].consistency_ratio < 0.1

    def test_e_topsis_scores_descending(self, three_job_scenario):
        """ranked_jobs should be in descending TOPSIS score order."""
        jobs_data, user = three_job_scenario
        result = _mini_pipeline(jobs_data, user, _plan_pairwise(), threshold=0.0)
        scores = [r["topsis_score"] for r in result["ranked"]]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]


# ===================================================================
# Full Scenario Walkthroughs — Real Catalog Data
# ===================================================================

class TestFullScenarioFrontendUser:
    """
    SCENARIO: A frontend user enters skills on the website.

    User skills:
        HTML        = average (0.6)
        CSS         = average (0.6)
        JavaScript  = advanced     (0.9)
        React       = advanced     (0.9)

    Preference (ascending importance): salary, skill_match, learning_effort, demand
        → demand is MOST important, salary is LEAST important.

    Pairwise (Saaty):
        (skill_match, salary)           = 3      skill_match 3× > salary
        (skill_match, demand)           = 1/5    demand 5× > skill_match
        (skill_match, learning_effort)  = 1/3    learning_effort 3× > skill_match
        (salary, demand)                = 1/7    demand 7× > salary
        (salary, learning_effort)       = 1/5    learning_effort 5× > salary
        (demand, learning_effort)       = 3      demand 3× > learning_effort

    5 jobs from the real catalog, threshold = 0.1.
    Backend Developer has 0 overlap → should be filtered.
    Among the 4 survivors, demand-heavy AHP should favour Frontend Dev or Full Stack Dev.
    """

    # Skill IDs (stable mapping for this scenario)
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
    DJANGO = 31
    LARAVEL = 32
    SPRING_BOOT = 33

    @pytest.fixture
    def scenario(self):
        user = {self.HTML: 0.6, self.CSS: 0.6, self.JS: 0.9, self.REACT: 0.9}

        jobs_data = [
            {   # Job 1 — Frontend Developer
                "job": JobRequirements(
                    1,
                    frozenset({self.HTML, self.CSS, self.JS,
                               self.RESPONSIVE, self.GIT, self.API_INTEG,
                               self.UIUX, self.BOOTSTRAP}),
                    (frozenset({self.REACT, self.ANGULAR, self.VUE}),),  # OR slot 0
                ),
                "salary": 13.5,
                "demand": 47,
            },
            {   # Job 2 — Full Stack Developer
                "job": JobRequirements(
                    2,
                    frozenset({self.HTML, self.CSS, self.JS,
                               self.DATABASE, self.SQL, self.NOSQL,
                               self.GIT, self.DOCKER, self.AWS,
                               self.RESTFUL, self.UNIT_TEST}),
                    tuple(),  # no OR slot
                ),
                "salary": 16.5,
                "demand": 68,
            },
            {   # Job 3 — JavaScript Developer
                "job": JobRequirements(
                    3,
                    frozenset({self.JS, self.NODEJS, self.REACT, self.VUE,
                               self.ANGULAR, self.GIT, self.HTML, self.CSS}),
                    tuple(),
                ),
                "salary": 18.0,
                "demand": 1,
            },
            {   # Job 4 — WordPress Developer
                "job": JobRequirements(
                    4,
                    frozenset({self.WORDPRESS, self.PHP, self.HTML,
                               self.CSS, self.JS, self.PLUGINS,
                               self.THEMES, self.MYSQL}),
                    tuple(),
                ),
                "salary": 16.5,
                "demand": 6,
            },
            {   # Job 5 — Backend Developer
                "job": JobRequirements(
                    5,
                    frozenset({self.PYTHON, self.JAVA, self.CSHARP,
                               self.REST_APIS, self.DATABASE, self.SQL,
                               self.DOCKER, self.GIT, self.AWS,
                               self.MICROSERVICES, self.SECURITY}),
                    (frozenset({self.NODEJS, self.DJANGO, self.LARAVEL, self.SPRING_BOOT}),),
                ),
                "salary": 14.5,
                "demand": 90,
            },
        ]

        pairwise = [
            PairwiseEntry("skill_match", "salary", 3),
            PairwiseEntry("skill_match", "demand", 1.0 / 5),
            PairwiseEntry("skill_match", "learning_effort", 1.0 / 3),
            PairwiseEntry("salary", "demand", 1.0 / 7),
            PairwiseEntry("salary", "learning_effort", 1.0 / 5),
            PairwiseEntry("demand", "learning_effort", 3),
        ]

        return jobs_data, user, pairwise

    # --- STEP 1+2: Similarity scores ---

    def test_step1_similarity_scores(self, scenario):
        """Verify cosine similarity matches hand-calculated values."""
        jobs_data, user, _ = scenario
        job_reqs = [d["job"] for d in jobs_data]
        vocab = build_vocab_skill_ids_ordered(job_reqs, user)

        scores = {}
        for d in jobs_data:
            jr = d["job"]
            bd = skill_match_breakdown(jr, user, vocab_skill_ids_ordered=vocab)
            scores[jr.job_id] = bd

        # Job 1 (Frontend): u·j=3.0 (HTML 0.6 + CSS 0.6 + JS 0.9 + React 0.9)
        assert scores[1]["dot_product_u_dot_j"] == pytest.approx(3.0)
        assert scores[1]["job_binary_skill_count"] == 11  # 8 mandatory + 3 framework alts
        assert scores[1]["score"] == pytest.approx(
            3.0 / (math.sqrt(2.34) * math.sqrt(11)), abs=0.005
        )

        # Job 2 (Full Stack): u·j=2.1 (HTML+CSS+JS), 11 binary skills
        assert scores[2]["dot_product_u_dot_j"] == pytest.approx(2.1)
        assert scores[2]["job_binary_skill_count"] == 11

        # Job 3 (JS Dev): u·j=3.0 (JS+React+HTML+CSS), 8 binary skills
        assert scores[3]["dot_product_u_dot_j"] == pytest.approx(3.0)
        assert scores[3]["job_binary_skill_count"] == 8

        # Job 4 (WordPress): u·j=2.1 (HTML+CSS+JS), 8 binary skills
        assert scores[4]["dot_product_u_dot_j"] == pytest.approx(2.1)
        assert scores[4]["job_binary_skill_count"] == 8

        # Job 5 (Backend): u·j=0 (no overlap)
        assert scores[5]["dot_product_u_dot_j"] == pytest.approx(0.0)
        assert scores[5]["score"] == pytest.approx(0.0)

        # Ordering: JS Dev > Frontend > WordPress > Full Stack >> Backend
        assert scores[3]["score"] > scores[1]["score"]
        assert scores[1]["score"] > scores[4]["score"]
        assert scores[4]["score"] > scores[2]["score"]
        assert scores[2]["score"] > scores[5]["score"]

    # --- STEP 3: Threshold filter ---

    def test_step3_threshold_drops_backend(self, scenario):
        """Backend Dev (score=0.0) fails threshold=0.1; 4 jobs survive."""
        jobs_data, user, pairwise = scenario
        result = _mini_pipeline(jobs_data, user, pairwise, threshold=0.1)
        surviving_ids = {c["job_id"] for c in result["candidates"]}
        assert surviving_ids == {1, 2, 3, 4}
        assert 5 not in surviving_ids

    # --- STEP 4: Learning effort ---

    def test_step4_learning_effort(self, scenario):
        """
        Job 1 (Frontend): missing responsive, git, api_integ, uiux, bootstrap=5; slot has React→0 → LE=5
        Job 2 (Full Stack): missing DB,SQL,NoSQL,git,docker,AWS,restful,unittest=8; no slot → LE=8
        Job 3 (JS Dev): missing Node.js,Vue,Angular,git=4; no slot → LE=4
        Job 4 (WordPress): missing WP,PHP,plugins,themes,MySQL=5; no slot → LE=5
        """
        jobs_data, user, pairwise = scenario
        result = _mini_pipeline(jobs_data, user, pairwise, threshold=0.1)
        effort = {c["job_id"]: c["learning_effort"] for c in result["candidates"]}
        assert effort[1] == 5
        assert effort[2] == 8
        assert effort[3] == 4
        assert effort[4] == 5

    # --- STEP 5: Decision matrix ---

    def test_step5_decision_matrix(self, scenario):
        """Verify the 4×4 decision matrix rows match expected values."""
        jobs_data, user, pairwise = scenario
        result = _mini_pipeline(jobs_data, user, pairwise, threshold=0.1)
        by_id = {c["job_id"]: c for c in result["candidates"]}

        # [SkillMatch, Salary, Demand, LearningEffort]
        assert by_id[1]["salary"] == pytest.approx(13.5)
        assert by_id[1]["demand"] == 47
        assert by_id[2]["salary"] == pytest.approx(16.5)
        assert by_id[2]["demand"] == 68
        assert by_id[3]["salary"] == pytest.approx(18.0)
        assert by_id[3]["demand"] == 1
        assert by_id[4]["salary"] == pytest.approx(16.5)
        assert by_id[4]["demand"] == 6

    # --- STEP 6: AHP weights ---

    def test_step6_ahp_weights(self, scenario):
        """
        Demand is most important → highest weight.
        Salary is least important → lowest weight.
        Weights sum to 1. CR < 0.1.
        """
        _, _, pairwise = scenario
        ahp = run_ahp(pairwise)

        assert sum(ahp.weights.values()) == pytest.approx(1.0)
        assert ahp.consistency_ratio < 0.1, f"CR={ahp.consistency_ratio} > 0.1 — inconsistent!"

        # Weight ordering must reflect user preference
        w = ahp.weights
        assert w["demand"] > w["learning_effort"], "demand should outweigh learning_effort"
        assert w["learning_effort"] > w["skill_match"], "learning_effort should outweigh skill_match"
        assert w["skill_match"] > w["salary"], "skill_match should outweigh salary"

        # demand should get the lion's share (>40%)
        assert w["demand"] > 0.40
        # salary should be tiny (<10%)
        assert w["salary"] < 0.10

    # --- STEP 7: TOPSIS ranking ---

    def test_step7_topsis_final_ranking(self, scenario):
        """
        With demand-heavy weights:
        - Frontend (demand=47) and Full Stack (demand=68) should be top 2.
        - JS Dev (demand=1) and WordPress (demand=6) should be bottom 2.
        - Scores must be in [0,1] and descending.
        """
        jobs_data, user, pairwise = scenario
        result = _mini_pipeline(jobs_data, user, pairwise, threshold=0.1)

        ranked = result["ranked"]
        assert len(ranked) == 4

        # Scores descending
        for i in range(len(ranked) - 1):
            assert ranked[i]["topsis_score"] >= ranked[i + 1]["topsis_score"]

        # All scores in [0, 1]
        for r in ranked:
            assert 0.0 <= r["topsis_score"] <= 1.0

        # Top 2 must be the high-demand jobs (Frontend=47, Full Stack=68)
        top2_ids = {ranked[0]["job_id"], ranked[1]["job_id"]}
        assert top2_ids == {1, 2}, f"Top 2 should be Frontend + Full Stack, got {top2_ids}"

        # Bottom 2 must be the low-demand jobs
        bottom2_ids = {ranked[2]["job_id"], ranked[3]["job_id"]}
        assert bottom2_ids == {3, 4}, f"Bottom 2 should be JS Dev + WordPress, got {bottom2_ids}"

    def test_step7_demand_shift_flips_winner(self, scenario):
        """
        If user switches preference to skill_match most important (instead of demand),
        JS Developer (best skill match, lowest effort) should rise to rank 1.
        """
        jobs_data, user, _ = scenario

        skill_first_pairwise = [
            PairwiseEntry("skill_match", "salary", 7),
            PairwiseEntry("skill_match", "demand", 5),
            PairwiseEntry("skill_match", "learning_effort", 3),
            PairwiseEntry("salary", "demand", 1.0 / 3),
            PairwiseEntry("salary", "learning_effort", 1.0 / 3),
            PairwiseEntry("demand", "learning_effort", 1.0 / 3),
        ]

        result = _mini_pipeline(jobs_data, user, skill_first_pairwise, threshold=0.1)
        ranked = result["ranked"]
        assert ranked[0]["job_id"] == 3, "JS Developer should win when skill_match is king"
