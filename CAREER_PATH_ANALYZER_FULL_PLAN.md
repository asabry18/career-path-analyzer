# Career Path & Skill Gap Analyzer — Project Overview & Status

---

## What this project is

A **full-stack Decision Support System (DSS)** that helps students and graduates discover career paths that fit their skills, compare roles on multiple criteria (match, salary, market demand, learning effort), and get a **minimum set of courses** to close skill gaps.

| Layer | Stack | Role |
|-------|--------|------|
| **Frontend** | React, TypeScript, Vite, Tailwind, Axios | Collect skills + priority ranking, call APIs, show ranked careers, gaps, framework choices, learning plan |
| **Backend** | Django 5, Django REST Framework, PostgreSQL | Catalog CRUD via API, stateless analysis endpoint |
| **DSS core** | Pure Python (`apps/dss/`) — NumPy, SciPy, PuLP | Similarity → threshold → AHP → TOPSIS → Set Cover (no Django imports) |

**In scope:** Stateless analysis, seeded job/skill/course catalog, REST API, integrated UI.  
**Out of scope (v1):** User accounts, saved analysis history, job scraping.

---

## Problem & purpose

Many graduates are unsure which career fits them. There is often a gap between **skills they have** and **what employers require**; salary and demand vary by role. This system:

1. Stores a **catalog** of jobs (salary, demand), mandatory skills, **framework alternatives** (OR slots), and courses linked to skills.
2. Accepts the user’s **skills with proficiency levels** and **ranked priorities** among four criteria.
3. Computes **skill match** (cosine similarity), filters weak matches, ranks survivors with **AHP + TOPSIS**, lists **gaps** and **optional frameworks**, and recommends a **Set Cover** learning plan.

---

## Implementation status (summary)

| Step | Area | Status | Notes |
|------|------|--------|--------|
| 1 | Django scaffold, settings, deps | **Done** | `backend/`, `config/settings/`, `requirements.txt`, `.env.example` |
| 2 | Apps & routing | **Done** | `catalog`, `analysis`, `apps/dss` |
| 3 | Catalog models & migrations | **Done** | Six models including `JobFrameworkAlternative` |
| 4 | Seed data | **Done** | `seed_catalog` from CSV in `backend/data/seed/` |
| 5 | Similarity | **Done** | Dense cosine on unified vocabulary; relaxed job binary vector (mandatory + all framework alts) |
| 6 | k-Means clustering | **Skipped** | Not in pipeline; flow goes similarity → AHP → TOPSIS directly |
| 7 | AHP & TOPSIS | **Done** | AHP eigenvector + CR; TOPSIS with **min–max** normalization, `learning_effort` as cost |
| 8 | Set Cover & pipeline | **Done** | `pipeline.py` orchestrates full flow; PuLP ILP |
| 9 | Catalog REST | **Done** | `GET /api/skills/`, `/api/jobs/`, `/api/courses/` |
| 10 | Analyze REST | **Done** | `POST /api/analyze/`; priorities → pairwise via ranking rules |
| 11 | Admin & OpenAPI | **Partial** | `drf-spectacular` in settings; **Django admin models not registered**; schema URL not wired in root `urls.py` |
| 12 | Docs & polish | **Partial** | Postman collection + pytest; **no root/backend README**; frontend README is Vite template only |
| — | Frontend ↔ API | **Done** | Axios, `AnalysisContext`, skills search, recommendations UI |

**Tests:** Pytest covers DSS modules (`similarity`, `ahp`, `topsis`, `setcover`, `pipeline` rules/integration) and `POST /api/analyze/` (`apps/analysis/tests.py`). Postman collection: `backend/postman/Career-Path-Analyzer-cosine-similarity.postman_collection.json`.

---

## Repository layout (actual)

```
career-path-analyzer/
  CAREER_PATH_ANALYZER_FULL_PLAN.md   ← this file
  backend/
    manage.py
    requirements.txt
    .env.example
    config/                 # settings, urls
    apps/
      catalog/              # models, admin (empty), serializers, views, seed_catalog
      analysis/             # analyze view, serializers, debug test endpoints
      dss/                  # pure Python DSS
        constants.py
        types.py
        similarity.py
        ahp.py
        topsis.py
        setcover.py
        pipeline.py
        tests/
    data/seed/              # CSV: jobs, skills taxonomy, courses
    postman/
  frontend/
    src/
      api/client.ts         # fetchSkills, analyze
      context/AnalysisContext.tsx
      pages/                # Skills, Priorities, Recommendations
      components/
      utils/mappers.ts
```

---

## Processing pipeline (runtime — as implemented)

Order in `apps/dss/pipeline.py`:

1. **Vocabulary** — sorted union of skill IDs from jobs + user.
2. **User vector** — declared skills mapped to weights (`beginner` 0.2, `under average` 0.4, `average` 0.6, `above average` 0.8, `advanced` 1.0).
3. **Skill match** — cosine similarity: user vector vs job **relaxed binary** vector (1 on each mandatory skill and each skill in any framework alternative). See `similarity.py`.
4. **Threshold** — drop jobs with `skill_match_score < threshold` (default `0.4`).
5. **Learning effort** (per job) — count of missing mandatory skills + count of framework slots where `max(user weight in slot) = 0`.
6. **Decision matrix** — columns: `skill_match`, `salary`, `demand`, `learning_effort`.
7. **AHP** — six pairwise comparisons → weights + consistency ratio `CR` (warn if `CR > 0.1`). Frontend sends a **priority ranking**; backend converts to Saaty pairwises via `pairwise_from_priority_ranking` (adjacent ranks → 3, one apart → 5, two apart → 7).
8. **TOPSIS** — column-wise **min–max** to [0,1] (benefit columns: higher better; `learning_effort`: cost, inverted); multiply by AHP weights; positive/negative ideal; Euclidean distances; closeness `C_i = D⁻/(D⁺+D⁻)`; rank descending.
9. **Gaps** — `missing_skills` (mandatory not in user profile); `optional_frameworks` (unsatisfied OR slots with all alternatives listed).
10. **Set Cover** — minimize selected courses covering union of missing skills (one representative skill per empty framework slot for cover set). Returns `learning_plan` with `selected_courses`, `covered_skills`, `uncovered_skills`.

**Not used:** k-Means (`clustering.py` does not exist; Step 6 intentionally skipped).

### Framework OR semantics

| Concern | Behavior |
|---------|----------|
| **Similarity (cosine)** | Relaxed bag: job vector has 1 on every mandatory skill and every framework alternative skill (document in thesis if comparing to strict per-slot max). |
| **Learning effort** | One unit per **unsatisfied slot** (not per alternative). |
| **API output** | `optional_frameworks`: `[{ slot_index, alternatives: [{ skill_id, name }] }]` when slot unsatisfied. |
| **Frontend** | Separate “Framework Choices — pick one” section per ranked job. |

### Decision criteria

Keys: `skill_match`, `salary`, `demand`, `learning_effort` — defined in `apps/dss/constants.py`.

---

## Database catalog

| Model | Purpose |
|-------|---------|
| **Skill** | `name` (unique) |
| **Job** | `title`, `description`, `avg_salary`, `demand_score` |
| **JobSkill** | Mandatory skill (AND) |
| **JobFrameworkAlternative** | OR slot: same `job_id` + `slot_index` = alternatives |
| **Course** | `title`, `url`, `provider` |
| **CourseSkill** | Course teaches skill |

Seed: `python manage.py seed_catalog` (optional `--purge`). CSVs under `backend/data/seed/`.

---

## API contract (implemented)

Base URL: `http://127.0.0.1:8000/api/` (dev). CORS enabled for frontend origin.

### Catalog

| Method | Path | Response |
|--------|------|------------|
| GET | `/skills/` | `[{ "id", "name" }]` |
| GET | `/jobs/` | Jobs with skills/frameworks (list serializer) |
| GET | `/courses/` | Courses with linked skills |

### Analyze

**`POST /api/analyze/`**

Request (frontend shape):

```json
{
  "skills": [
    { "name": "HTML", "level": "Average" },
    { "name": "JavaScript", "level": "Advanced" }
  ],
  "priorities": ["demand", "learn", "match", "salary"],
  "threshold": 0.4
}
```

- `priorities`: exactly **4 unique** ids, **most important first**: `match` → `skill_match`, `learn` → `learning_effort`, `salary`, `demand`.
- Skill `name` matched case-insensitively to catalog; unknown names → `400`.

Response (summary):

```json
{
  "ahp": {
    "weights": { "skill_match": 0.12, "salary": 0.06, "demand": 0.56, "learning_effort": 0.26 },
    "lambda_max": 4.08,
    "consistency_ratio": 0.05,
    "consistency_ok": true
  },
  "ranked_jobs": [
    {
      "rank": 1,
      "job_id": 1,
      "title": "Frontend Developer",
      "description": "...",
      "topsis_score": 0.69,
      "skill_match_score": 0.59,
      "avg_salary": 13.5,
      "demand_score": 47,
      "learning_effort": 5,
      "missing_skills": [{ "skill_id": 7, "name": "Responsive Design" }],
      "optional_frameworks": []
    }
  ],
  "learning_plan": {
    "selected_courses": [{ "course_id": 1, "title": "...", "provider": "...", "url": "...", "skills": [...] }],
    "covered_skills": [...],
    "uncovered_skills": [...],
    "solver_status": "Optimal"
  },
  "meta": { "vocab_size": 35, "jobs_evaluated": 20, "jobs_after_threshold": 4 }
}
```

### Debug / test endpoints (dev)

Under `/api/test/`: `catalog-stats`, `cosine-example`, `similarity-preview`, `pipeline-preview` — see `apps/analysis/debug_views.py`.

---

## Frontend flow

1. **Home** → **Skills** — live search against `GET /skills/`; add skills + levels from the catalog list.
2. **Priorities** — drag/rank four criteria; **Analyze** calls `POST /analyze/`.
3. **Recommendations** — top careers (TOPSIS), detail, mandatory gaps + courses, **framework choices**, **recommended learning plan** (Set Cover courses + skill chips).

Env: `VITE_API_URL` (default `http://127.0.0.1:8000/api`).

---

## Libraries

| Need | Library |
|------|---------|
| Vectors, cosine | NumPy |
| AHP eigenpair | NumPy `linalg.eig` |
| Set Cover | PuLP |
| Web API | Django, DRF, django-cors-headers |
| DB | psycopg (PostgreSQL) |
| API schema (configured, not fully exposed) | drf-spectacular |
| Tests | pytest, pytest-django |
| Frontend HTTP | axios |

---

## How to run (development)

**Backend**

```bash
cd backend
python -m venv .venv
# activate venv
pip install -r requirements.txt
# configure .env / DATABASE
python manage.py migrate
python manage.py seed_catalog
python manage.py runserver
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Tests**

```bash
cd backend
pytest
```

---

## Original execution steps (reference)

The project was built following Steps 1–12 below. Use **`Execute Step N`** only for **remaining** work.

| Step | Title | Status |
|------|--------|--------|
| 1 | Project scaffold | Done |
| 2 | Django apps and routing | Done |
| 3 | Catalog models and migrations | Done |
| 4 | Seed data | Done |
| 5 | DSS similarity | Done (relaxed cosine; not per-slot max in cosine) |
| 6 | k-Means clustering | **Skipped** |
| 7 | AHP and TOPSIS | Done |
| 8 | Set Cover and pipeline | Done |
| 9 | REST catalog endpoints | Done |
| 10 | REST analyze endpoint | Done |
| 11 | Admin and OpenAPI | Partial — register models in admin; add `/api/schema/` to urls |
| 12 | Polish | Partial — add project README, example curl, optional Spectacular UI |

### Remaining polish (suggested)

- Register catalog models in `apps/catalog/admin.py`.
- Wire `drf-spectacular` schema + Swagger in `config/urls.py`.
- Add `backend/README.md` (and/or root README) with setup, seed, analyze example.
- Align thesis text with: skipped k-Means, min–max TOPSIS, relaxed cosine vs strict OR-slot matching if needed.

---

## Design notes for thesis / review

1. **TOPSIS normalization:** Implementation uses **min–max** per column (not vector normalization \(r_{ij} = x_{ij}/\sqrt{\sum x_{ij}^2}\)). Suited to mixed scales, few alternatives, and explicit cost handling for `learning_effort`.
2. **Priority → AHP:** User ranks four criteria; backend generates Saaty pairwises (gaps 0/1/2 → intensities 3/5/7).
3. **Similarity vs gaps:** Cosine uses relaxed job encoding; gap detection and learning effort use strict slot/mandatory rules in `pipeline.py`.

---

*This document supersedes the original backend-only plan: it reflects the integrated React frontend, skipped clustering, actual API payloads, and current completion status.*
