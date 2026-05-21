"""Request / response serializers for ``POST /api/analyze/``."""

from rest_framework import serializers

from apps.dss.constants import CRITERIA_KEYS

# ── Frontend criteria id → backend criteria key ──────────────────────
_PRIORITY_ID_TO_CRITERIA = {
    "salary": "salary",
    "demand": "demand",
    "match": "skill_match",
    "learn": "learning_effort",
}

VALID_PRIORITY_IDS = tuple(_PRIORITY_ID_TO_CRITERIA.keys())


def map_priority_ids_to_criteria(priority_ids: list[str]) -> list[str]:
    """Translate frontend priority ids to internal CRITERIA_KEYS order."""
    return [_PRIORITY_ID_TO_CRITERIA[pid] for pid in priority_ids]


# ── Request ──────────────────────────────────────────────────────────


class SkillInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    level = serializers.ChoiceField(
        choices=[
            "Beginner",
            "Under Average",
            "Average",
            "Above Average",
            "Advanced",
        ]
    )


class AnalyzeRequestSerializer(serializers.Serializer):
    skills = SkillInputSerializer(many=True, min_length=1)
    priorities = serializers.ListField(
        child=serializers.ChoiceField(choices=VALID_PRIORITY_IDS),
        min_length=4,
        max_length=4,
        help_text="Ordered list of priority ids from most to least important.",
    )
    threshold = serializers.FloatField(default=0.4, min_value=0.0, max_value=1.0)

    def validate_priorities(self, value):
        if len(set(value)) != 4:
            raise serializers.ValidationError("All 4 priorities must be unique.")
        return value


# ── Response (nested) ────────────────────────────────────────────────


class SkillRefSerializer(serializers.Serializer):
    skill_id = serializers.IntegerField()
    name = serializers.CharField()


class FrameworkSlotSerializer(serializers.Serializer):
    slot_index = serializers.IntegerField()
    alternatives = SkillRefSerializer(many=True)


class CourseSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    title = serializers.CharField()
    provider = serializers.CharField()
    url = serializers.URLField()
    skills = SkillRefSerializer(many=True)


class RankedJobSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    job_id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    topsis_score = serializers.FloatField()
    skill_match_score = serializers.FloatField()
    avg_salary = serializers.FloatField()
    demand_score = serializers.IntegerField()
    learning_effort = serializers.IntegerField()
    missing_skills = SkillRefSerializer(many=True)
    optional_frameworks = FrameworkSlotSerializer(many=True)


class AhpSerializer(serializers.Serializer):
    weights = serializers.DictField(child=serializers.FloatField())
    lambda_max = serializers.FloatField()
    consistency_ratio = serializers.FloatField()
    consistency_ok = serializers.BooleanField()


class LearningPlanSerializer(serializers.Serializer):
    selected_courses = CourseSerializer(many=True)
    covered_skills = SkillRefSerializer(many=True)
    uncovered_skills = SkillRefSerializer(many=True)
    solver_status = serializers.CharField()


class AnalyzeResponseSerializer(serializers.Serializer):
    ahp = AhpSerializer()
    ranked_jobs = RankedJobSerializer(many=True)
    learning_plan = LearningPlanSerializer()
    meta = serializers.DictField()
