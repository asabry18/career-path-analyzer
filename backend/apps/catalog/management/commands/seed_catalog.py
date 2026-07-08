import ast
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import (
    Course,
    CourseSkill,
    Job,
    JobFrameworkAlternative,
    JobSkill,
    Skill,
)

DEFAULT_FILENAMES = {
    "jobs_skills": "jobs skills.csv",
    "jobs": "jobs_with_sector.csv",
    "courses": "Courses.csv",
}


def canonical_skill_label(raw: str) -> str:
    return " ".join(raw.strip().split()).lower()


def parse_skills_list(cell: str) -> list[str]:
    cell = (cell or "").strip()
    if not cell:
        return []
    try:
        value = ast.literal_eval(cell)
    except (SyntaxError, ValueError):
        inner = cell.strip()
        if inner.startswith("[") and inner.endswith("]"):
            inner = inner[1:-1]
        parts = [p.strip().strip("'\"") for p in inner.split(",")]
        value = [p for p in parts if p]
    if not isinstance(value, list):
        return []
    labels: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        label = canonical_skill_label(item)
        if label:
            labels.append(label)
    return labels


def parse_sector(cell: str) -> str | None:
    cell = (cell or "").strip()
    if not cell:
        return None
    if cell.startswith("[") and cell.endswith("]"):
        try:
            value = ast.literal_eval(cell)
            if isinstance(value, list) and value:
                cell = str(value[0])
            elif isinstance(value, str):
                cell = value
        except (SyntaxError, ValueError):
            cell = cell[1:-1].strip().strip("'\"")
    parts = [p.strip() for p in cell.split(",") if p.strip()]
    if not parts:
        return None
    return ", ".join(parts)


def split_frameworks(cell: str) -> list[str]:
    if not cell or not str(cell).strip():
        return []
    labels: list[str] = []
    for chunk in str(cell).split(","):
        label = canonical_skill_label(chunk)
        if label:
            labels.append(label)
    return labels


class Command(BaseCommand):
    help = (
        "Load catalog data from CSV files in data/seed (idempotent upsert per job URL/title). "
        "Use --reset to delete and reseed only courses data from Courses.csv."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Delete all catalog rows before seeding.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Delete all existing Course and CourseSkill records, then reseed "
                "only from Courses.csv. Other catalog data (jobs, skills) is untouched."
            ),
        )
        parser.add_argument(
            "--seed-dir",
            type=Path,
            default=None,
            help="Directory containing CSV files (default: BASE_DIR/data/seed).",
        )

    def handle(self, *args, **options):
        seed_dir: Path = options["seed_dir"] or Path(settings.BASE_DIR) / "data" / "seed"
        seed_dir = seed_dir.resolve()
        if not seed_dir.is_dir():
            raise CommandError(f"Seed directory not found: {seed_dir}")

        # --reset: only reseed courses
        if options["reset"]:
            courses_csv = seed_dir / DEFAULT_FILENAMES["courses"]
            if not courses_csv.is_file():
                raise CommandError(
                    f"Courses CSV file not found: {courses_csv}"
                )
            with transaction.atomic():
                self._reset_courses()
                distinct_urls, new_cs_links = self._seed_courses(courses_csv)
            self.stdout.write(
                self.style.SUCCESS(
                    "Courses reset complete. "
                    f"Distinct course URLs in CSV: {distinct_urls}; "
                    f"course-to-skill links created: {new_cs_links}."
                )
            )
            return

        jobs_skills = seed_dir / DEFAULT_FILENAMES["jobs_skills"]
        jobs_csv = seed_dir / DEFAULT_FILENAMES["jobs"]
        courses_csv = seed_dir / DEFAULT_FILENAMES["courses"]
        missing = [p.name for p in (jobs_skills, jobs_csv, courses_csv) if not p.is_file()]
        if missing:
            raise CommandError(
                "Missing CSV file(s): " + ", ".join(missing) + f" under {seed_dir}"
            )

        with transaction.atomic():
            if options["purge"]:
                self._purge_catalog()

            created_skills = self._seed_taxonomy_skills(jobs_skills)
            job_count, link_count, fw_count = self._seed_jobs(jobs_csv)
            distinct_urls, new_cs_links = self._seed_courses(courses_csv)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. "
                f"New skills from taxonomy file: {created_skills}. "
                f"Jobs upserted: {job_count}; mandatory links (re)written: {link_count}; "
                f"framework alternative rows (re)written: {fw_count}. "
                f"Distinct course URLs in CSV: {distinct_urls}; "
                f"new course-to-skill links this run: {new_cs_links}."
            )
        )

    def _purge_catalog(self) -> None:
        CourseSkill.objects.all().delete()
        Course.objects.all().delete()
        JobSkill.objects.all().delete()
        JobFrameworkAlternative.objects.all().delete()
        Job.objects.all().delete()
        Skill.objects.all().delete()
        self.stdout.write(self.style.WARNING("Catalog tables emptied (--purge)."))

    def _reset_courses(self) -> None:
        """Delete all CourseSkill and Course records, leaving jobs and skills intact."""
        cs_count, _ = CourseSkill.objects.all().delete()
        c_count, _ = Course.objects.all().delete()
        self.stdout.write(
            self.style.WARNING(
                f"Courses reset: deleted {c_count} course(s) and {cs_count} course-skill link(s)."
            )
        )

    def _get_or_create_skill(self, label: str) -> tuple[Skill, bool]:
        return Skill.objects.get_or_create(name=label)

    def _seed_taxonomy_skills(self, path: Path) -> int:
        created = 0
        with path.open(newline="", encoding="utf-8-sig") as fh:
            for line_no, raw in enumerate(fh, start=1):
                name = raw.strip()
                if not name or line_no == 1 and name.lower() == "skills":
                    continue
                label = canonical_skill_label(name)
                if not label:
                    continue
                _, was_created = self._get_or_create_skill(label)
                if was_created:
                    created += 1
        return created

    def _seed_jobs(self, path: Path) -> tuple[int, int, int]:
        jobs_touched = 0
        total_job_skills = 0
        total_fw = 0
        with path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            for row in reader:
                title_raw = row.get("cleaned_title") or row.get("\ufeffcleaned_title") or ""
                title = title_raw.strip()
                if not title:
                    self.stderr.write(self.style.WARNING("Skipping row without title"))
                    continue

                try:
                    demand = int(float(row["demand"]))
                    avg_salary = float(row["avg_salary"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise CommandError(f"Bad demand/salary row for '{title}': {exc}") from exc

                salary_band = (row.get("salary_month") or "").strip()
                description_parts = []
                if salary_band:
                    description_parts.append(f"Salary band: {salary_band}")
                description = "\n".join(description_parts)

                skills = parse_skills_list(row.get("skills", ""))
                sector = parse_sector(row.get("Sector") or row.get("sector") or "")

                job, _ = Job.objects.update_or_create(
                    title=title,
                    defaults={
                        "demand_score": demand,
                        "avg_salary": avg_salary,
                        "description": description,
                        "sector": sector,
                    },
                )
                jobs_touched += 1

                JobSkill.objects.filter(job=job).delete()
                JobFrameworkAlternative.objects.filter(job=job).delete()

                for label in skills:
                    skill, _ = self._get_or_create_skill(label)
                    JobSkill.objects.create(job=job, skill=skill)
                    total_job_skills += 1

                slot_labels = split_frameworks(row.get("frameworks", ""))
                slot_index = 0
                for label in slot_labels:
                    skill, _ = self._get_or_create_skill(label)
                    JobFrameworkAlternative.objects.create(
                        job=job,
                        skill=skill,
                        slot_index=slot_index,
                    )
                    total_fw += 1

        return jobs_touched, total_job_skills, total_fw

    def _seed_courses(self, path: Path) -> tuple[int, int]:
        cs_created = 0
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            expected = {"skill", "course_name", "link", "platform"}
            if reader.fieldnames:
                fields = {f.strip().lower() for f in reader.fieldnames}
                if not expected.issubset(fields):
                    raise CommandError(
                        f"Courses.csv must have columns {sorted(expected)}, got {reader.fieldnames}"
                    )

            seen_urls: set[str] = set()
            for row in reader:
                skill_raw = (row.get("skill") or "").strip()
                title = (row.get("course_name") or "").strip()
                url = (row.get("link") or "").strip()
                provider = (row.get("platform") or "").strip()
                if not url:
                    continue
                label = canonical_skill_label(skill_raw)
                skill, _ = self._get_or_create_skill(label)
                dup_key = url.lower()
                if dup_key not in seen_urls:
                    Course.objects.update_or_create(
                        url=url,
                        defaults={"title": title or url, "provider": provider},
                    )
                    seen_urls.add(dup_key)

                course = Course.objects.get(url=url)
                _, cs_was_created = CourseSkill.objects.get_or_create(
                    course=course,
                    skill=skill,
                )
                if cs_was_created:
                    cs_created += 1

        return len(seen_urls), cs_created
