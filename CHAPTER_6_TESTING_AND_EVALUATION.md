# Chapter 6: Testing and Evaluation

This chapter presents the testing strategy, specific test cases, and a comprehensive manual walkthrough of the system's core algorithms to ensure reliability, accuracy, and mathematical integrity.

## 6.1 Testing Strategy

The project employs a tiered testing strategy to verify different layers of the system:
*   **Unit Testing:** Pure Python tests using `pytest` to verify the mathematical correctness of individual DSS modules (`ahp.py`, `topsis.py`, `similarity.py`, `setcover.py`). These tests run without a database or web server.
*   **Integration Testing:** Django REST Framework `APITestCase` classes are used to verify the interaction between the API endpoints, the database, and the DSS pipeline.
*   **End-to-End (Functional) Testing:** Manual verification of the React frontend to ensure data flows correctly from user input to the final recommendations.
*   **Validation Testing:** Checking the Analytic Hierarchy Process (AHP) for consistency using the Consistency Ratio ($CR < 0.1$).

## 6.2 Test Cases and Results

The following table summarizes key test cases executed to validate the system.

| Test ID | Component | Description | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| TC-01 | AHP | Provide 4 ranked criteria (Match, Salary, Demand, Effort). | Weights sum to 1.0; Match weight > Salary weight. | Passed |
| TC-02 | AHP | Input inconsistent priorities causing $CR > 0.1$. | System flags `consistency_ok: false`. | Passed |
| TC-03 | Similarity | User with 100% match of mandatory skills. | Skill match score = 1.0 (or very close due to float precision). | Passed |
| TC-04 | TOPSIS | Multiple job candidates with varying scores. | Jobs ranked correctly based on closeness to ideal solution ($C_i$). | Passed |
| TC-05 | Set Cover | Missing skills covered by multiple available courses. | Solver selects the minimum number of courses to cover all gaps. | Passed |
| TC-06 | API | POST `/api/analyze/` with valid payload. | HTTP 200 OK with full JSON results (AHP, Rank, Plan). | Passed |
| TC-07 | API | POST `/api/analyze/` with unknown skill names. | HTTP 400 Bad Request with error detail "Unknown skills". | Passed |
| TC-08 | System | Threshold filtering ($threshold = 0.5$). | Jobs with match < 0.5 are excluded from final rankings. | Passed |

## 6.3 Manual Walkthrough & Algorithmic Validation

To validate the system's logic, a full scenario was calculated by hand. This walkthrough traces the transformation of user input into ranked career paths.

### 6.3.1 Scenario Inputs
*   **User Skills:** HTML (0.6), CSS (0.6), JavaScript (0.9), React (0.9).
*   **User Preferences (Least to Most Important):** 
    1. Salary
    2. Skill Match
    3. Learning Effort
    4. Market Demand (Most Important)

### 6.3.2 Step 1 & 2: Skill Vocabulary and Vectorization
The vocabulary (size $N=33$) is constructed from all skills in the sampled jobs.
*   **User Vector $u$:** Weights applied at dimensions corresponding to HTML, CSS, JS, and React.
*   **Norm calculation:** $\|u\| = \sqrt{0.6^2 + 0.6^2 + 0.9^2 + 0.9^2} \approx 1.5297$

**Similarity Calculation ($Cosine = \frac{u \cdot j}{\|u\| \times \|j\|}$):**
*   **Job 1 (Frontend Developer):** $\|j_1\| \approx 3.3166$, $u \cdot j_1 = 3.0 \implies \text{Score} = \mathbf{0.5912}$
*   **Job 3 (JS Developer):** $\|j_3\| \approx 2.8284$, $u \cdot j_3 = 3.0 \implies \text{Score} = \mathbf{0.6932}$

### 6.3.3 Step 4: Learning Effort Calculation
Learning effort is calculated as the count of missing mandatory skills and unsatisfied framework slots.
- **Job 1:** 5 missing mandatory skills; React satisfies the framework slot. **Effort = 5**.
- **Job 3:** 4 missing mandatory skills. **Effort = 4**.

### 6.3.4 Step 6: AHP Criterion Weighting
Based on the preference: **Demand > Effort > Match > Salary**, Saaty's pairwise comparison matrix yields:
| Criterion | Weight |
| :--- | :--- |
| **Market Demand** | ~0.5765 |
| **Learning Effort** | ~0.2473 |
| **Skill Match** | ~0.1188 |
| **Salary** | ~0.0574 |
*Validation: $\lambda_{max} \approx 4.12$, $CR \approx 0.044 < 0.1$ (Consistent).*

### 6.3.5 Step 7: TOPSIS Ranking
Applying Min-Max normalization and AHP weights to the Decision Matrix results in the final Closeness Coefficients ($C$):

| Rank | Job Title | TOPSIS Score ($C$) | Logic |
| :--- | :--- | :--- | :--- |
| **1** | **Frontend Developer** | **0.6849** | Balanced high demand and reasonable match. |
| **2** | **Full Stack Developer**| **0.6775** | Highest demand (68) but penalized by high effort (8). |
| **3** | **JS Developer** | **0.3272** | Best match but crippled by low demand (1). |
| **4** | **WordPress Dev** | **0.2653** | Low demand and significant gaps. |

**Key Insight:** Even though the JS Developer job has the highest skill match, the user's high preference for *Market Demand* (57% weight) correctly pushed Frontend Developer to the top rank.

## 6.4 Performance Evaluation

### 6.4.1 Algorithm Efficiency
*   **Similarity calculation:** $O(N \times M)$ where $N$ is the number of jobs and $M$ is the vocabulary size. Using NumPy vectorization ensures sub-millisecond execution for thousands of jobs.
*   **AHP Weighting:** $O(C^2)$ where $C$ is the number of criteria (constant at 4).
*   **Set Cover (PuLP):** Integer Linear Programming handles typical gaps in under 100ms.

### 6.4.2 System Latency
Average response time for the `/api/analyze/` endpoint is measured at **150ms - 300ms** on standard development hardware.

## 6.5 Limitations and Known Issues

### 6.5.1 Limitations
*   **Data Freshness:** System relies on a seeded catalog; no real-time scraping.
*   **Simple Weighting:** Proficiency levels map linearly (0.2 to 1.0).
*   **Statelessness:** No analysis history is saved between sessions.

### 6.5.2 Known Issues
*   **Exact Matching:** Typographic errors in skill names in manual API calls lead to 400 errors.
*   **Framework Skew:** The "relaxed-bag" cosine implementation counts every potential framework, which can slightly inflate the match score regardless of the number of frameworks required.
