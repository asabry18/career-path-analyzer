# Career Path & Skill Gap Analyzer — Backend Specification & Execution Plan

Attach this file in a new Cursor chat (`@docs/CAREER_PATH_ANALYZER_FULL_PLAN.md`) when implementing

**How to run the plan:** Say exactly: **`Execute Step 1`** — complete that step fully before moving to Step 2. Repeat until all steps are done.

---

## Part A — Project description and purpose

### Problem

Many students and graduates are unsure which career path fits them. There is often a gap between the skills they have and what employers ask for; salary and demand differ across markets. People may waste effort on skills that do not align with roles they could realistically pursue.

### Purpose

Build the **backend** for a web-based **Decision Support System** that:

1. Uses **catalog data** stored in PostgreSQL: job roles (with salary and demand indicators), **mandatory** skills per job, **framework alternatives** (OR slots), skills taxonomy, and courses linked to skills.
2. Accepts **stateless** requests: the user’s chosen skills with **levels** (mapped to numeric weights), plus **pairwise preferences** between decision criteria.
3. Computes **skill match** combining **mandatory** requirements with **framework slots** where **only one** of several listed frameworks is needed (see below — not naive cosine across all framework dimensions).
4. Filters weak matches, assigns **career clusters** with **k-Means**, builds a **multi-criteria decision matrix**, derives weights with **AHP**, ranks alternatives with **TOPSIS**, lists mandatory gaps and **optional framework choices**, and solves **Set Cover** for courses.

### Framework columns in the dataset (OR semantics)

Some jobs include a **frameworks** field (e.g. React, Vue, Angular for front-end roles). Employers typically expect **one** of those stacks, **not all**.

**Matching**

- **`JobSkill` rows:** AND semantics — each listed skill contributes like a normal requirement to similarity (weighted user vs mandatory binary vector).
- **`JobFrameworkAlternative` rows** (same `job_id` + `slot_index` = one OR slot): contribution uses \(\max_{t \in \text{slot}} u_t\) — **one score per slot**, not a sum over every alternative.
- Each framework slot counts as **one logical requirement** when normalizing so having Vue alone satisfies “needs a JS framework” like having Python satisfies “needs Python.”

**Recommendations**

- If \(\max_{t \in \text{slot}} u_t = 0\): count **one** unit toward **learning_effort** for that slot (not one per framework).
- Return **`optional_frameworks`** on each ranked job: list every alternative in unsatisfied slots so the UI can offer “pick any one path” plus courses per skill where available.

### Scope boundaries

| In scope | Out of scope (v1) |
|----------|-------------------|
| REST API consumed by React/TS frontend | User accounts, JWT sessions |
| Persist **catalog**: jobs, skills, mandatory links, framework alternatives, courses | Saving analysis history per visitor |
| Stateless `POST /api/analyze/` | Job scraping pipelines |

---

## Part B — Algorithms and tools

### Processing pipeline (runtime order)

1. Build **skill vocabulary** from every skill appearing in `JobSkill` or **`JobFrameworkAlternative`**.
2. For each job load **mandatory** skill IDs (`JobSkill`) and **framework slots** (`JobFrameworkAlternative` grouped by `slot_index`).
3. Build **user vector** \(u\): \(u_s =\) mapped weight if declared, else \(0\).
4. **Skill match score:** combine (a) cosine-style alignment on **mandatory-only** dimensions with (b) **per-slot max**: for each framework slot add \(\max_{t \in \text{slot}} u_t\) as fulfilling **one** logical requirement; normalize so each slot equals **one** unit of demand (implement precisely in `similarity.py`, unit-tested — includes guards for zero norms).
5. **Threshold:** drop jobs below cutoff on **skill_match_score**.
6. **k-Means:** job rows as binary vectors over skills — **1** if skill is mandatory **or** appears in any framework alternative (relaxed bag for clustering only; document in thesis). Assign user’s vector in same space for centroid distance.
7. **Decision matrix:** SkillMatch | Salary | Demand | LearningEffort — where LearningEffort = *(mandatory skills missing)* + *(framework slots still completely unmatched)*.
8. **AHP:** build \(4\times4\) pairwise matrix from six comparisons → principal eigenvector → normalized weights; compute **consistency ratio** \(CR\) (warn if \(CR > 0.1\)).
9. **TOPSIS:** weighted normalized matrix → positive/negative ideal → Euclidean distances → closeness \(C_i \in [0,1]\); higher is better.
10. **Gaps:** mandatory skills absent from user → listed under **`missing_skills`**. Framework slots with \(\max_{t\in\text{slot}} u_t = 0\) → **`optional_frameworks`** listing every alternative skill id/name (user picks one track).
11. Union of skills still missing for Set Cover → **Set Cover** minimize \(\sum x_c\) (cover mandatory gaps; optionally include **one** representative skill per empty framework slot — document chosen rule in code).

### User skill level → weight mapping

Centralize in `apps/dss/constants.py`:

| Level | Weight |
|-------|--------|
| beginner | `0.3` |
| intermediate | `0.6` |
| advanced | `0.9` |
| not declared | `0.0` |

Accept numeric floats from the frontend if needed; validate range `[0, 1]`.

### Decision criteria keys

`skill_match`, `salary`, `demand`, `learning_effort` — used in pairwise payloads and internally.

### Recommended libraries

| Need | Library | Role |
|------|---------|------|
| Vector ops, cosine, normalization | **NumPy** | Core linear algebra |
| Largest eigenpair for AHP | **SciPy** (`scipy.linalg.eig`) or NumPy power iteration | Weights + \(\lambda_{\max}\) for \(CR\) |
| k-Means | **scikit-learn** (`sklearn.cluster.KMeans`) | Cluster job vectors |
| Set Cover IP | **PuLP** (`pulp`) | CBC solver bundled |
| Web framework | **Django ≥ 5**, **djangorestframework** | API |
| DB adapter | **psycopg** (`psycopg[binary]`) | PostgreSQL |
| API schema UI | **drf-spectacular** | OpenAPI / Swagger |
| CORS | **django-cors-headers** | Frontend on another origin |
| Testing | **pytest**, **pytest-django**, **factory-boy** | Unit + API tests |

Cosine-style algebra uses **NumPy**; mandatory vs framework-slot logic stays explicit in code so OR semantics are not lost inside a single dense dot product.

---

## Part C — Database catalog

Six reference tables (framework OR slots):

| Model | Fields (conceptual) |
|-------|---------------------|
| **Skill** | `id`, `name` (unique) |
| **Job** | `id`, `title`, `description`, `avg_salary`, `demand_score` |
| **JobSkill** | FK job, FK skill — **mandatory** requirement (AND) |
| **JobFrameworkAlternative** | FK job, FK skill, **`slot_index`** (small int ≥ 0) — rows sharing `(job_id, slot_index)` are **alternatives**; exactly **one** satisfies that slot |
| **Course** | `id`, `title`, `url`, `provider` |
| **CourseSkill** | FK course, FK skill — many-to-many |

Constraint suggestion: `UNIQUE(job_id, slot_index, skill_id)`. Seed/import maps dataset **frameworks** column → multiple rows per slot.

Optional later: `Skill.category`, `Job.region`.

---

## Part D — API contract (draft)

**`GET /api/skills/`** → `[{ "id", "name" }]`

**`GET /api/jobs/`** → optional list/browse for admin or UI.

**`POST /api/analyze/`** — body example:

```json
{
  "skills": [
    { "skill_id": 12, "level": "intermediate" },
    { "skill_id": 15, "level": "advanced" }
  ],
  "pairwise": [
    { "a": "skill_match", "b": "salary", "value": 3 },
    { "a": "skill_match", "b": "demand", "value": 5 },
    { "a": "skill_match", "b": "learning_effort", "value": 7 },
    { "a": "salary", "b": "demand", "value": 3 },
    { "a": "salary", "b": "learning_effort", "value": 5 },
    { "a": "demand", "b": "learning_effort", "value": 3 }
  ],
  "threshold": 0.4,
  "n_clusters": 5
}
```

Response includes at minimum: `weights`, `consistency_ratio`, `cluster`, `ranked_jobs` (each with `topsis_score`, `skill_match_score`, `learning_effort`, `missing_skills`, **`optional_frameworks`** — see below), `learning_plan` from Set Cover.

**`optional_frameworks` (per ranked job)** — example shape:

```json
"optional_frameworks": [
  {
    "slot_index": 0,
    "alternatives": [
      { "skill_id": 101, "name": "React" },
      { "skill_id": 102, "name": "Vue" },
      { "skill_id": 103, "name": "Angular" }
    ]
  }
]
```

Omitted or empty array when every framework slot has \(\max_{t\in\text{slot}} u_t > 0\).

Align field names with the frontend when it is linked.

---

## Part E — Repository layout (target)

```
career-path-analyzer-backend/
  manage.py
  requirements.txt
  .env.example
  README.md
  config/
    settings/base.py dev.py prod.py
    urls.py wsgi.py asgi.py
  apps/
    catalog/          # models, admin, serializers, views, urls
    analysis/       # serializers + analyze view only (no DB models)
    dss/            # pure Python — NO Django imports
      constants.py
      similarity.py
      clustering.py
      ahp.py
      topsis.py
      setcover.py
      pipeline.py
      types.py
      tests/
  data/seed/        # skills.json, jobs.json, courses.json (or CSV ingestion)
```

---

## Part F — Execution steps (for the agent)

Complete each step before asking for the next. After Step 1 succeeds, say **`Execute Step 2`**, and so on.

### Step 1 — Project scaffold

- Create Django project under `config/` (or equivalent single settings package).
- Add `requirements.txt` with: Django≥5, djangorestframework, django-cors-headers, psycopg[binary], drf-spectacular, python-dotenv, numpy, scipy, scikit-learn, pulp, pytest, pytest-django, factory-boy.
- Add `.env.example` (`DATABASE_URL` or discrete `DB_*`, `SECRET_KEY`, `DEBUG`).
- Split settings `base.py` / `dev.py`; enable `REST_FRAMEWORK`, `CORS_ALLOWED_ORIGINS` placeholder.
- **Done when:** `python manage.py check` passes and development server starts.

### Step 2 — Django apps and routing

- Create apps `catalog`, `analysis`; create package `apps/dss` (add `apps` to `PYTHONPATH` or install as editable — choose pattern used by team).
- Wire root `urls.py` to include `/api/` routes (placeholder views OK).
- **Done when:** project loads URLs without error.

### Step 3 — Catalog models and migrations

- Implement `Skill`, `Job`, `JobSkill`, **`JobFrameworkAlternative`**, `Course`, `CourseSkill` as specified in Part C.
- Run migrations against PostgreSQL (or document SQLite only for local smoke — production target is Postgres).
- **Done when:** `migrate` succeeds and models appear in Django shell.

### Step 4 — Seed data

- Add `management/commands/seed_catalog.py` loading `data/seed/*.json` (or CSV). Map **`frameworks`** column into **`JobFrameworkAlternative`**: frameworks listed together for one job → **one `slot_index`** (e.g. 0) with one row per framework skill; separate slots if multiple disjoint OR groups appear in schema later.
- Ensure each framework string resolves to a `Skill`; mandatory skills → `JobSkill`.
- **Done when:** seed runs idempotently enough for dev repeat (`flush` + seed or upsert logic).

### Step 5 — DSS core: similarity (mandatory + framework slots)

- Implement `constants.py`, `types.py`.
- Implement `similarity.py`: vocabulary from mandatory + framework skills; **mandatory** match (cosine or equivalent segment); **framework slots** via \(\max\) per slot; single **`skill_match_score`** ∈ \([0,1]\); unit tests including **one job with OR slot** (user knows Vue only → slot satisfied; user knows none → optional_frameworks populated downstream).
- **Done when:** pytest passes for similarity module.

### Step 6 — DSS: clustering

- Implement `clustering.py`: binary job rows — **1** on skill \(s\) if mandatory **or** \(s\) appears in any **`JobFrameworkAlternative`** for that job (relaxed representation for clustering).
- Fit `KMeans` on that matrix; cache centroids keyed by catalog version/hash where practical; assign user vector in same skill space to nearest centroid.
- Unit tests with fixed random seed.
- **Done when:** pytest passes.

### Step 7 — DSS: AHP and TOPSIS

- Implement `ahp.py`: pairwise list → comparison matrix → eigenvector weights + \(CR\).
- Implement `topsis.py`: benefit vs cost columns; min-max normalization input; weighted TOPSIS; return sorted indices + closeness scores.
- Unit tests with small numerical fixtures.
- **Done when:** pytest passes.

### Step 8 — DSS: Set Cover and pipeline

- Implement `setcover.py` with PuLP: binary \(x_c\), cover constraints per missing skill.
- Implement `pipeline.py`: orchestrate similarity → threshold → clustering meta → matrix (**LearningEffort** uses mandatory gaps + unmatched framework slots) → AHP → TOPSIS → **`missing_skills`** + **`optional_frameworks`** → Set Cover per Part B rules.
- Integration-style unit test on miniature catalog fixture.
- **Done when:** pytest passes for pipeline.

### Step 9 — REST: catalog endpoints

- DRF serializers/viewsets or APIViews for `GET /api/skills/`, `GET /api/jobs/`.
- Register routes under `catalog/urls.py`.
- **Done when:** browsable API or curl returns JSON.

### Step 10 — REST: analyze endpoint

- Request/response serializers in `analysis/` matching Part D.
- View loads catalog from DB into DTOs, calls `pipeline.run(...)`, returns JSON.
- Handle validation errors (unknown skill IDs, inconsistent pairwise).
- **Done when:** `POST /api/analyze/` returns coherent ranking + `learning_plan` on seeded DB.

### Step 11 — Admin and documentation

- Register catalog models in Django admin.
- Add `drf-spectacular` — `/api/schema/` and Swagger UI.
- **Done when:** admin usable and schema generates.

### Step 12 — Polish

- README: setup, env vars, migrate, seed, run server, example curl.
- Optional: pytest integration hitting analyze API.
- **Done when:** another developer can follow README end-to-end.

---

## Start here

Tell the agent:

> **`Execute Step 1`** according to `@docs/CAREER_PATH_ANALYZER_FULL_PLAN.md`.

---

*Last updated: mandatory skills + framework OR slots (`JobFrameworkAlternative`); similarity uses max-per-slot; optional_frameworks in API; execution Steps 1–12.*
