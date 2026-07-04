# Chapter 5: Implementation

This chapter details the technical realization of the Career Path & Skill Gap Analyzer. It covers the implementation environment, the core Decision Support System (DSS) logic, and provides samples of the system's output.

## 5.1 Implementation Environment and Setup

The project is built using a decoupled architecture consisting of a Python/Django backend and a React/TypeScript frontend.

### 5.1.1 Hardware and Operating System
*   **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu 22.04+ recommended).
*   **Processor:** Intel Core i5 / AMD Ryzen 5 or higher.
*   **Memory:** Minimum 8GB RAM.
*   **Storage:** At least 2GB of available disk space.

### 5.1.2 Software Stack
*   **Backend:** Python 3.12+, Django 5.x, Django REST Framework.
*   **Frontend:** Node.js 20+, React 19, Vite, Tailwind CSS.
*   **Database:** PostgreSQL (Production) or SQLite (Development).
*   **Math/DSS Libraries:** NumPy, SciPy, PuLP (Integer Linear Programming).

### 5.1.3 Setup Procedure
1.  **Backend Initialization:**
    ```bash
    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py seed_catalog
    ```
2.  **Frontend Initialization:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
3.  **Environment Configuration:** A `.env` file is used to manage sensitive keys such as `SECRET_KEY`, `DATABASE_URL`, and `CORS_ALLOWED_ORIGINS`.

---

## 5.2 Key Implementation Details

The core logic resides in the `backend/apps/dss/` directory, implemented as a pure Python module independent of the web framework to ensure mathematical integrity and testability.

### 5.2.1 Processing Pipeline
The system executes a multi-stage pipeline when a user requests an analysis:
1.  **Vocabulary Construction:** A unified vocabulary of skills is built from the union of user-declared skills and skills required by all jobs in the catalog.
2.  **Vectorization:**
    *   **User Vector:** Skills are mapped to weights: Beginner (0.2), Under Average (0.4), Average (0.6), Above Average (0.8), and Advanced (1.0).
    *   **Job Vector (Relaxed Binary):** A "relaxed-bag" approach is used where mandatory skills and *all* framework alternatives are marked as 1.
3.  **Similarity Match:** Cosine similarity is calculated between the user and job vectors. Jobs falling below a threshold (default 0.3) are filtered out.

### 5.2.2 Analytic Hierarchy Process (AHP)
AHP is used to derive weights from the user’s priority ranking.
*   **Pairwise Conversion:** The user's ranked criteria (e.g., Match > Salary > Demand > Effort) are converted into Saaty's scale pairwise comparisons.
*   **Weight Calculation:** The system computes the principal eigenvector of the comparison matrix.
*   **Consistency Check:** A Consistency Ratio (CR) is calculated; if $CR > 0.1$, the weights are flagged as inconsistent.

### 5.2.3 TOPSIS Ranking
The survivors of the similarity filter are ranked using TOPSIS:
*   **Normalization:** Min-Max normalization is applied to each column of the decision matrix (`skill_match`, `salary`, `demand`, `learning_effort`).
*   **Weighting:** Normalized values are multiplied by AHP weights.
*   **Distance Calculation:** Euclidean distances to the Positive Ideal Solution (PIS) and Negative Ideal Solution (NIS) are computed.
*   **Closeness Coefficient:** Alternatives are ranked by $C_i = D_i^- / (D_i^+ + D_i^-)$.

### 5.2.4 Learning Plan (Set Cover)
The "Set Cover" problem is solved using Integer Linear Programming (ILP) via the PuLP library.
*   **Objective:** Minimize the number of courses required to cover the union of missing mandatory skills and at least one alternative for each missing framework slot.

---

## 5.3 Sample Screenshots / Output Samples

*This section provides visual evidence of the system's functionality.*

### 5.3.1 Skill Input Interface
[Insert Screenshot 1: Show the "Skills" page with search results and several added skills with proficiency sliders.]
*Description: User selecting skills from the catalog and assigning proficiency levels.*

### 5.3.2 Priority Ranking
[Insert Screenshot 2: Show the "Priorities" page with the four criteria (Match, Salary, Demand, Effort) being dragged/sorted.]
*Description: The drag-and-drop interface for user-defined multi-criteria priority.*

### 5.3.3 Ranked Recommendations
[Insert Screenshot 3: Show the list of ranked career results with TOPSIS scores and "Match" percentages.]
*Description: The primary output of the system showing careers ranked by their closeness to the ideal solution.*

### 5.3.4 Detailed Skill Gap and Learning Plan
[Insert Screenshot 4: Show a specific career detail view, highlighting "Missing Skills" and the "Recommended Courses" section.]
*Description: The personalized learning plan derived via the Set Cover algorithm.*
