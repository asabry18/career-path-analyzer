"""Integration tests for POST /api/analyze/ endpoint."""

import pytest
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.catalog.models import (
    Course,
    CourseSkill,
    Job,
    JobFrameworkAlternative,
    JobSkill,
    Skill,
)


@pytest.mark.django_db
class TestAnalyzeEndpoint(APITestCase):
    """Verify the full /api/analyze/ endpoint against a tiny in-memory catalog."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            email="tester@example.com",
            password="strong-password-123",
            first_name="Test",
            last_name="User",
        )
        cls.html = Skill.objects.create(name="HTML")
        cls.css = Skill.objects.create(name="CSS")
        cls.js = Skill.objects.create(name="JavaScript")
        cls.react = Skill.objects.create(name="React")
        cls.vue = Skill.objects.create(name="Vue")
        cls.angular = Skill.objects.create(name="Angular")
        cls.node = Skill.objects.create(name="Node.js")
        cls.python = Skill.objects.create(name="Python")
        cls.django_skill = Skill.objects.create(name="Django")

        cls.frontend = Job.objects.create(
            title="Frontend Developer", avg_salary=5000, demand_score=7,
        )
        JobSkill.objects.create(job=cls.frontend, skill=cls.html)
        JobSkill.objects.create(job=cls.frontend, skill=cls.css)
        JobSkill.objects.create(job=cls.frontend, skill=cls.js)
        JobFrameworkAlternative.objects.create(
            job=cls.frontend, skill=cls.react, slot_index=0,
        )
        JobFrameworkAlternative.objects.create(
            job=cls.frontend, skill=cls.vue, slot_index=0,
        )
        JobFrameworkAlternative.objects.create(
            job=cls.frontend, skill=cls.angular, slot_index=0,
        )

        cls.backend = Job.objects.create(
            title="Backend Developer", avg_salary=6000, demand_score=5,
        )
        JobSkill.objects.create(job=cls.backend, skill=cls.python)
        JobSkill.objects.create(job=cls.backend, skill=cls.django_skill)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_valid_request_returns_200(self):
        payload = {
            "skills": [
                {"name": "HTML", "level": "Advanced"},
                {"name": "CSS", "level": "Average"},
                {"name": "JavaScript", "level": "Average"},
                {"name": "React", "level": "Beginner"},
            ],
            "priorities": ["match", "salary", "demand", "learn"],
            "threshold": 0.0,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ahp", data)
        self.assertIn("ranked_jobs", data)
        self.assertIn("learning_plan", data)
        self.assertIn("meta", data)
        self.assertTrue(data["ahp"]["consistency_ok"])
        self.assertGreater(len(data["ranked_jobs"]), 0)

    def test_ranked_jobs_have_correct_fields(self):
        payload = {
            "skills": [
                {"name": "HTML", "level": "Beginner"},
                {"name": "CSS", "level": "Beginner"},
                {"name": "JavaScript", "level": "Beginner"},
            ],
            "priorities": ["salary", "demand", "match", "learn"],
            "threshold": 0.0,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        job = resp.json()["ranked_jobs"][0]
        for field in ("rank", "job_id", "title", "topsis_score",
                       "skill_match_score", "avg_salary", "demand_score",
                       "learning_effort", "missing_skills", "optional_frameworks"):
            self.assertIn(field, job)

    def test_ahp_weights_match_priority_order(self):
        payload = {
            "skills": [{"name": "HTML", "level": "Beginner"}],
            "priorities": ["salary", "demand", "match", "learn"],
            "threshold": 0.0,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        w = resp.json()["ahp"]["weights"]
        self.assertGreater(w["salary"], w["demand"])
        self.assertGreater(w["demand"], w["skill_match"])
        self.assertGreater(w["skill_match"], w["learning_effort"])

    def test_threshold_filters_jobs(self):
        payload = {
            "skills": [{"name": "Python", "level": "Advanced"}],
            "priorities": ["match", "salary", "demand", "learn"],
            "threshold": 0.9,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        titles = [j["title"] for j in resp.json()["ranked_jobs"]]
        self.assertNotIn("Frontend Developer", titles)

    def test_unknown_skill_returns_400(self):
        payload = {
            "skills": [{"name": "Nonexistent", "level": "Beginner"}],
            "priorities": ["match", "salary", "demand", "learn"],
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Unknown skills", resp.json()["detail"])

    def test_missing_priorities_returns_400(self):
        payload = {
            "skills": [{"name": "HTML", "level": "Beginner"}],
            "priorities": ["match", "salary"],
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_priorities_returns_400(self):
        payload = {
            "skills": [{"name": "HTML", "level": "Beginner"}],
            "priorities": ["match", "match", "salary", "demand"],
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_learning_plan_present(self):
        payload = {
            "skills": [
                {"name": "HTML", "level": "Advanced"},
                {"name": "CSS", "level": "Advanced"},
                {"name": "JavaScript", "level": "Advanced"},
            ],
            "priorities": ["match", "salary", "demand", "learn"],
            "threshold": 0.0,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
        lp = resp.json()["learning_plan"]
        self.assertIn("selected_courses", lp)
        self.assertIn("solver_status", lp)

    def test_skill_name_case_insensitive(self):
        payload = {
            "skills": [{"name": "html", "level": "Beginner"}],
            "priorities": ["match", "salary", "demand", "learn"],
            "threshold": 0.0,
        }
        resp = self.client.post("/api/analyze/", payload, format="json")
        self.assertEqual(resp.status_code, 200)
