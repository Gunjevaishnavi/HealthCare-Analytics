# Project 23: Healthcare Analytics and Patient Risk Indicator System

**Difficulty:** Advanced  
**Domain:** Healthcare Informatics & Operational Data Analytics  
**Deployment URL:** [http://127.0.0.1:5050](http://127.0.0.1:5050)

---

> [!CAUTION]
> ### MANDATORY EDUCATIONAL SCOPE & NON-CLINICAL LIMITATIONS STATEMENT
> **Educational analytics only.** All data within this system is synthetically generated or de-identified.  
> **Risk indicators and machine learning scores are transparent computational flags for observational review and resource planning — they are NOT medical diagnoses and must NEVER be used to make real patient-care decisions, clinical triage, or treatment recommendations.**

---

## 1. Executive Summary & Objective

This system processes de-identified and synthetic patient cohorts to compute transparent, documented, rule-based indicators alongside comprehensive hospital operational analytics. It bridges clinical data validation, data engineering, statistical profiling, and machine learning while strictly adhering to safety guardrails and explicit non-clinical boundaries.

### Key Capabilities
- **REST APIs:** Full programmatic CRUD for synthetic patient and visit records, measurement ingestion, and rule-based indicator evaluations.
- **Physiological Range Validation:** Automated classification of vital signs and biomarkers against documented sample reference intervals and biological plausibility bounds (`VALID`, `OUT_OF_RANGE_HIGH`, `OUT_OF_RANGE_LOW`, `IMPLAUSIBLE_VALUE`).
- **Department Admissions & Workload Analytics:** Pandas-powered aggregation tracking emergency vs. elective intakes, bed capacity, and average length of stay (LoS) across 8 hospital units.
- **Transparent Rule Engine:** Fully auditable, rule-based indicator system with documented thresholds and rationale.
- **Parametric & Non-Parametric Statistics:** NumPy computation of mean, standard deviation, median, IQR, 5th/95th percentiles, and skewness across all physiological parameters.
- **Headless Visualization:** Matplotlib generation of department workload trends, vital distributions with reference bands, rule frequencies, and biomarker correlation heatmaps.
- **Educational Machine Learning Benchmark:** Scikit-Learn supervised classification (Logistic Regression and Random Forest) evaluating multi-indicator propensity with ROC-AUC, 5-fold cross-validation, confusion matrices, and explicit non-clinical labeling.
- **Access Restriction:** Protected by session authentication and HTTP header API key enforcement (`X-API-Key: health-demo-key-2026`).

---

## 2. Relational Database Schema (MySQL & SQLite)

The schema implements the suggested entities and relationships. DDL statements are located in [`data/schema.sql`](data/schema.sql).

```
                      +-------------------+
                      |    departments    |
                      +-------------------+
                      | department_id(PK) |
                      | department_name   |
                      | wing              |
                      | capacity          |
                      +---------+---------+
                                | 1
                                |
                                | N
+-------------------+ 1       N +-------------------+
|     patients      +-----------+      visits       |
+-------------------+           +-------------------+
| patient_id (PK)   |           | visit_id (PK)     |
| age_band          |           | patient_id (FK)   |
| gender            |           | department_id (FK)|
| ethnicity_code    |           | visit_date        |
| residence_region  |           | discharge_date    |
| chronic_condition |           | admission_type    |
| created_at        |           | status            |
+---+---------------+           +---------+---------+
    | 1                                   | 1
    |                                     |
    | N                                   | N
+---+---------------+           +---------+---------+
|  risk_indicators  |           |   measurements    |
+-------------------+           +-------------------+
| indicator_id (PK) |           | measurement_id(PK)|
| patient_id (FK)   |           | patient_id (FK)   |
| rule_code         |           | visit_id (FK)     |
| indicator_value   |           | measurement_date  |
| indicator_category|           | measure_type      |
| rationale         |           | value             |
| created_at        |           | unit              |
+-------------------+           | is_valid_range    |
                                | validation_status |
                                +-------------------+
```

---

## 3. Documented Physiological Validation Assumptions

The validation engine screens measurements against clinical reference intervals and physiological plausibility limits:

| Parameter | Unit | Standard Reference Interval | Plausible Biological Range | Documented Sample Assumption Notes |
|:---|:---:|:---:|:---:|:---|
| `systolic_bp` | mmHg | 90 - 120 | 50 - 260 | Resting adult cuff reading. <50 or >260 mmHg indicates transducer failure. |
| `diastolic_bp` | mmHg | 60 - 80 | 30 - 150 | Correlated resting metric. <30 or >150 mmHg flagged as implausible artifact. |
| `heart_rate` | bpm | 60 - 100 | 30 - 220 | Adult resting pulse. <60 indicates bradycardia, >100 tachycardia. |
| `respiratory_rate`| breaths/min | 12 - 20 | 6 - 60 | Rested spontaneous breathing. >24 bpm represents tachypneic pattern. |
| `body_temp` | °C | 36.1 - 37.2 | 32.0 - 43.0 | Core temperature. <35.5 °C hypothermia suspicion; >38.0 °C febrile pattern. |
| `spo2` | % | 95 - 100 | 50 - 100 | Pulse oximetry on ambient air. <=92% warrants operational review. |
| `blood_glucose` | mg/dL | 70 - 99 | 30 - 600 | Overnight fasting state. >=126 mg/dL flagged as illustrative glycemic marker. |
| `bmi` | kg/m² | 18.5 - 24.9 | 12.0 - 75.0 | Calculated weight/height². >=30.0 classified as obesity class benchmark. |
| `creatinine` | mg/dL | 0.6 - 1.2 | 0.2 - 18.0 | Renal metabolic filtration marker. >=1.5 mg/dL flagged for clearance review. |

---

## 4. Transparent Rule-Based Indicator System

The system implements 5 transparent, auditable indicators with documented logic:

- **`R-VIT-01` (Cardiovascular Vital Stress Indicator):**
  - *Logic:* `Systolic BP >= 140 mmHg OR Heart Rate >= 105 bpm`
  - *Category:* Cardiovascular
  - *Rationale:* Identifies elevated hemodynamic stress or autonomic activation for cohort grouping.
- **`R-GLU-02` (Metabolic Glycemic Screening Indicator):**
  - *Logic:* `Fasting Glucose >= 126 mg/dL OR (Glucose >= 100 mg/dL AND BMI >= 30.0 kg/m²)`
  - *Category:* Metabolic
  - *Rationale:* Flags prospective metabolic syndrome patterns in synthetic cohorts.
- **`R-RES-03` (Respiratory Compromise Watch Indicator):**
  - *Logic:* `SpO2 <= 92% OR Respiratory Rate >= 24 breaths/min`
  - *Category:* Respiratory
  - *Rationale:* Captures ventilatory stress and potential hypoxemia patterns.
- **`R-REN-04` (Renal Clearance Screening Indicator):**
  - *Logic:* `Serum Creatinine >= 1.5 mg/dL`
  - *Category:* Renal
  - *Rationale:* Flags synthetic renal filtration abnormalities for non-clinical cohort grouping.
- **`R-COM-05` (Multisystem Composite Watch Indicator):**
  - *Logic:* `Co-occurrence of >= 2 individual indicators active`
  - *Category:* Composite
  - *Rationale:* Highlights multisystem operational vulnerability across departments for hospital resource planning.

---

## 5. Educational Machine Learning Benchmark (Scikit-Learn)

A strictly educational experiment comparing supervised statistical classifiers:
- **Task:** Predict composite multisystem review flag (`R-COM-05`) from baseline vital sign measurements (`systolic_bp`, `diastolic_bp`, `heart_rate`, `respiratory_rate`, `spo2`, `blood_glucose`, `bmi`, `creatinine`).
- **Models:**
  1. *Logistic Regression:* L2-regularized with standard scaling; reports feature odds ratios ($e^\beta$).
  2. *Random Forest Classifier:* 100 estimators; computes relative Gini feature importances.
- **Evaluation:** Accuracy, Precision, Recall, F1-score, Test ROC-AUC (~0.88), 5-Fold Stratified Cross-Validation, and Confusion Matrix.
- **Visuals:** Headless Matplotlib generation of ROC and Precision-Recall diagnostic curves saved to [`static/charts/ml_roc_pr_curve.png`](static/charts/ml_roc_pr_curve.png).

---

## 6. Access Restriction & Credentials

Per project criteria, access is restricted across both Web UI and REST API channels:

| Access Method | Identifier | Secret / Key | Role |
|:---|:---|:---|:---|
| **Web UI Login** | `analyst` | `Password123!` | Healthcare Data Analyst |
| **REST API Header** | `X-API-Key` | `health-demo-key-2026` | Healthcare Analyst (Demo) |
| **Admin API Key** | `X-API-Key` | `admin-key-sec-99` | System Administrator |

---

## 7. REST API Quick Reference

### List Patients
```bash
curl -s -H "X-API-Key: health-demo-key-2026" "http://127.0.0.1:5050/api/v1/patients?limit=5"
```

### Validate Physiological Measurement (Ad-hoc)
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"measure_type": "systolic_bp", "value": 155.0}' \
  "http://127.0.0.1:5050/api/v1/measurements/validate"
```

### Submit New Measurement (Triggers Auto-Validation & Rule Update)
```bash
curl -s -X POST -H "Content-Type: application/json" -H "X-API-Key: health-demo-key-2026" \
  -d '{"patient_id": "PAT-SYN-0001", "measure_type": "systolic_bp", "value": 145.0}' \
  "http://127.0.0.1:5050/api/v1/measurements"
```

### Fetch Operational Analytics Report
```bash
curl -s -H "X-API-Key: health-demo-key-2026" "http://127.0.0.1:5050/api/v1/analytics/operational-summary"
```

### Fetch Educational ML Evaluation Metrics
```bash
curl -s -H "X-API-Key: health-demo-key-2026" "http://127.0.0.1:5050/api/v1/ml/educational-evaluation"
```

---

## 8. Quickstart & Verification

```bash
# 1. Activate Python virtual environment
source .venv/bin/activate

# 2. Run unit and integration test suite
python -m unittest discover tests

# 3. Launch the Healthcare Analytics application
python run.py
```

Open your browser to: **[http://127.0.0.1:5050](http://127.0.0.1:5050)**  
Sign in using username `analyst` and password `Password123!`, or explore the interactive API documentation at [http://127.0.0.1:5050/api-docs](http://127.0.0.1:5050/api-docs).
