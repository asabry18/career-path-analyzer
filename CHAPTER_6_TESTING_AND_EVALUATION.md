# Chapter 6: Testing and Evaluation

This chapter presents the testing strategy, specific test cases, and an evaluation of the Career Path & Skill Gap Analyzer to ensure its reliability, accuracy, and performance.

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

## 6.3 Performance Evaluation

### 6.3.1 Algorithm Efficiency
*   **Similarity calculation:** $O(N \times M)$ where $N$ is the number of jobs and $M$ is the vocabulary size. Using NumPy vectorization ensures sub-millisecond execution for thousands of jobs.
*   **AHP Weighting:** $O(C^2)$ where $C$ is the number of criteria. Since $C=4$, this is constant time and extremely fast.
*   **Set Cover (PuLP):** While Set Cover is NP-hard, the "branch and cut" solver in PuLP handles typical job gaps (5-20 skills) in under 100ms.

### 6.3.2 System Latency
Average response time for the `/api/analyze/` endpoint (including database fetch, DSS pipeline, and Set Cover) is measured at **150ms - 300ms** on standard hardware, providing a seamless user experience.

## 6.4 Limitations and Known Issues

### 6.4.1 Limitations
*   **Data Freshness:** The system relies on a seeded catalog. It does not currently scrape real-time job postings or course updates.
*   **Simple Weighting:** The proficiency levels for user skills (Beginner to Advanced) are mapped to fixed linear weights (0.2 to 1.0).
*   **Statelessness:** Since the system is stateless (per current design), user analysis history is lost once the session ends unless manually saved.

### 6.4.2 Known Issues
*   **Case Sensitivity:** While the API handles skill matching case-insensitively, exact string matching is required; typos in skill names during manual API calls lead to errors.
*   **Framework OR Logic:** In the current similarity implementation (relaxed-bag), having *any* of the framework skills helps the score, but the logic does not penalize having multiple frameworks, which might slightly skew the similarity vs. actual learning effort.
