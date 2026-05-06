from collections import defaultdict

from rest_framework import serializers

from apps.catalog.models import Course, Job, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ("id", "name")


class JobListSerializer(serializers.ModelSerializer):
    mandatory_skills = serializers.SerializerMethodField()
    framework_slots = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            "id",
            "title",
            "description",
            "avg_salary",
            "demand_score",
            "mandatory_skills",
            "framework_slots",
        )

    def get_mandatory_skills(self, obj):
        pairs = sorted(
            ((js.skill_id, js.skill.name) for js in obj.job_skills.all()),
            key=lambda t: (t[1].lower(), t[0]),
        )
        return [{"id": pk, "name": name} for pk, name in pairs]

    def get_framework_slots(self, obj):
        slot_map = defaultdict(list)
        for fa in obj.framework_alternatives.all():
            slot_map[int(fa.slot_index)].append(
                {"id": fa.skill_id, "name": fa.skill.name}
            )
        for key in slot_map:
            slot_map[key].sort(key=lambda x: (x["name"].lower(), x["id"]))
        return [slot_map[k] for k in sorted(slot_map)]


class CourseListSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "title", "provider", "url", "skills")

    def get_skills(self, obj):
        pairs = sorted(
            ((cs.skill_id, cs.skill.name) for cs in obj.course_skills.all()),
            key=lambda t: (t[1].lower(), t[0]),
        )
        return [{"id": pk, "name": name} for pk, name in pairs]
