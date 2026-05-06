from django.db import models


class Skill(models.Model):
    """Taxonomy skill; unique by name."""

    name = models.CharField(max_length=255, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Job(models.Model):
    """Job role with salary and demand indicators for multi-criteria analysis."""

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    avg_salary = models.FloatField(
        help_text="Average or representative salary figure (catalog units).",
    )
    demand_score = models.PositiveIntegerField(
        help_text="Demand indicator (e.g. frequency rank from source data).",
    )

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class JobSkill(models.Model):
    """Mandatory skill for a job (AND semantics)."""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="job_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="job_skills",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "skill"],
                name="catalog_jobskill_job_skill_uniq",
            ),
        ]
        verbose_name = "job skill (mandatory)"
        verbose_name_plural = "job skills (mandatory)"


class JobFrameworkAlternative(models.Model):
    """
    One row per alternative skill in an OR slot.
    Rows sharing the same (job, slot_index) are alternatives; the user needs at most one.
    """

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="framework_alternatives",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="framework_alternatives",
    )
    slot_index = models.PositiveSmallIntegerField(
        help_text="Alternatives with the same job and slot_index form one OR group.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["job", "slot_index", "skill"],
                name="catalog_jobframework_job_slot_skill_uniq",
            ),
        ]


class Course(models.Model):
    title = models.CharField(max_length=500)
    url = models.URLField(max_length=2000)
    provider = models.CharField(max_length=255)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


class CourseSkill(models.Model):
    """Links a course to a skill it teaches (many-to-many via explicit join)."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="course_skills",
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="course_skills",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "skill"],
                name="catalog_courseskill_course_skill_uniq",
            ),
        ]
