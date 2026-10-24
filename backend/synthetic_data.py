"""
Synthetic Healthcare Record Generator
--------------------------------------
Generates realistic, de-identified synthetic patient cohorts, clinical visits,
vital measurement panels, and pre-computed transparent risk indicators.
Strictly synthetic: no real patient data is generated or used.
"""

import random
import datetime
import uuid
from typing import List, Dict
import numpy as np

from backend.database import SessionLocal, init_db, Department, Patient, Visit, Measurement, RiskIndicator
from backend.rules_engine import validate_measurement_value, evaluate_patient_indicators, MEASUREMENT_SPECS

DEPARTMENTS_DATA = [
    {"department_id": "DEP-EMERG", "department_name": "Emergency Department", "wing": "East Wing Ground", "capacity": 60},
    {"department_id": "DEP-CARD", "department_name": "Cardiology Clinic", "wing": "North Tower 4F", "capacity": 45},
    {"department_id": "DEP-INTMED", "department_name": "Internal Medicine", "wing": "West Wing 3F", "capacity": 55},
    {"department_id": "DEP-PULM", "department_name": "Pulmonology & Respiratory", "wing": "North Tower 2F", "capacity": 35},
    {"department_id": "DEP-PEDI", "department_name": "Pediatrics Unit", "wing": "South Pavilion 1F", "capacity": 40},
    {"department_id": "DEP-ONCO", "department_name": "Oncology Day Center", "wing": "Cancer Pavilion 2F", "capacity": 30},
    {"department_id": "DEP-ORTHO", "department_name": "Orthopedics & Sports Medicine", "wing": "East Wing 2F", "capacity": 40},
    {"department_id": "DEP-NEURO", "department_name": "Neurology Care Unit", "wing": "West Wing 5F", "capacity": 35}
]

AGE_BANDS = ["0-17", "18-35", "36-50", "51-65", "66-80", "80+"]
AGE_BAND_WEIGHTS = [0.08, 0.22, 0.25, 0.23, 0.15, 0.07]
GENDERS = ["Male", "Female", "Non-Binary", "Undisclosed"]
GENDER_WEIGHTS = [0.48, 0.49, 0.02, 0.01]
ETHNICITY_CODES = ["ETH_A1", "ETH_B2", "ETH_C3", "ETH_D4", "ETH_E5"]
REGIONS = ["Metro-North", "Urban-Central", "Suburban-East", "Rural-West", "Coastal-South"]
ADMISSION_TYPES = ["Emergency", "Elective", "Urgent", "Routine Outpatient"]
ADMISSION_WEIGHTS = [0.35, 0.20, 0.15, 0.30]


def seed_synthetic_data(num_patients: int = 200, min_visits_per_patient: int = 1, max_visits_per_patient: int = 5):
    """Populates the database with realistic de-identified synthetic healthcare data."""
    init_db()
    db = SessionLocal()

    try:
        # Check if departments already exist
        if db.query(Department).count() == 0:
            for dept_info in DEPARTMENTS_DATA:
                dept = Department(**dept_info)
                db.add(dept)
            db.commit()

        # If patients already exist, don't re-seed
        if db.query(Patient).count() >= num_patients:
            return

        dept_ids = [d["department_id"] for d in DEPARTMENTS_DATA]
        base_date = datetime.datetime.now() - datetime.timedelta(days=90)

        random.seed(42)
        np.random.seed(42)

        patients_created = []

        for i in range(1, num_patients + 1):
            pat_id = f"PAT-SYN-{i:04d}"
            age_band = np.random.choice(AGE_BANDS, p=AGE_BAND_WEIGHTS)
            gender = np.random.choice(GENDERS, p=GENDER_WEIGHTS)
            ethnicity = random.choice(ETHNICITY_CODES)
            region = random.choice(REGIONS)
            
            # Higher probability of chronic condition for older age bands
            chronic_prob = 0.15 if age_band in ["0-17", "18-35"] else (0.40 if age_band == "36-50" else 0.65)
            chronic_flag = bool(random.random() < chronic_prob)
            
            enroll_days = random.randint(0, 180)
            created_at = base_date - datetime.timedelta(days=enroll_days)

            patient = Patient(
                patient_id=pat_id,
                age_band=age_band,
                gender=gender,
                ethnicity_code=ethnicity,
                residence_region=region,
                chronic_condition_flag=chronic_flag,
                created_at=created_at
            )
            db.add(patient)
            patients_created.append((patient, age_band, chronic_flag))

        db.commit()

        # Generate visits and measurements
        total_visits = 0
        total_measurements = 0

        for patient, age_band, chronic_flag in patients_created:
            num_visits = random.randint(min_visits_per_patient, max_visits_per_patient)
            patient_latest_measures: Dict[str, float] = {}

            # Age band modifiers for realistic synthetic biological distributions
            is_older = age_band in ["51-65", "66-80", "80+"]
            base_sbp = 135 if is_older else 118
            base_glucose = 115 if chronic_flag else 92
            base_creat = 1.15 if is_older else 0.85

            for v_idx in range(1, num_visits + 1):
                v_id = f"VIS-{patient.patient_id}-{v_idx:02d}"
                days_offset = random.randint(0, 89)
                visit_dt = base_date + datetime.timedelta(days=days_offset, hours=random.randint(8, 20), minutes=random.randint(0, 59))
                
                dept_id = random.choice(dept_ids)
                if age_band == "0-17":
                    dept_id = "DEP-PEDI" if random.random() < 0.75 else "DEP-EMERG"
                elif chronic_flag and random.random() < 0.4:
                    dept_id = random.choice(["DEP-CARD", "DEP-INTMED", "DEP-PULM"])

                adm_type = np.random.choice(ADMISSION_TYPES, p=ADMISSION_WEIGHTS)
                stay_hours = random.randint(2, 72) if adm_type in ["Emergency", "Urgent"] else random.randint(1, 4)
                discharge_dt = visit_dt + datetime.timedelta(hours=stay_hours)

                visit = Visit(
                    visit_id=v_id,
                    patient_id=patient.patient_id,
                    department_id=dept_id,
                    visit_date=visit_dt,
                    discharge_date=discharge_dt,
                    admission_type=adm_type,
                    status="Completed"
                )
                db.add(visit)
                total_visits += 1

                # Generate measurements for this visit
                # 1. Systolic BP
                sbp_val = float(np.random.normal(base_sbp, 16))
                # 2. Diastolic BP (correlated with systolic)
                dbp_val = float(0.55 * sbp_val + np.random.normal(12, 6))
                # 3. Heart Rate
                hr_val = float(np.random.normal(78, 14))
                # 4. SpO2
                spo2_val = float(min(100.0, np.random.normal(97.5, 2.5)))
                # 5. Respiratory Rate
                rr_val = float(np.random.normal(16, 3.5))
                # 6. Blood Glucose
                glu_val = float(np.random.normal(base_glucose, 25))
                # 7. Body Temperature
                temp_val = float(np.random.normal(36.8, 0.5))
                # 8. BMI
                bmi_val = float(np.random.normal(27.0, 5.0))
                # 9. Creatinine
                creat_val = float(max(0.4, np.random.normal(base_creat, 0.35)))

                # Introduce intentional plausible & implausible anomalies in 2-3% of synthetic data
                # to demonstrate validation features and robustness
                if random.random() < 0.02:
                    sbp_val = 285.0 # Implausible high
                elif random.random() < 0.015:
                    spo2_val = 42.0 # Implausible low

                measurements_pool = [
                    ("systolic_bp", sbp_val, "mmHg"),
                    ("diastolic_bp", dbp_val, "mmHg"),
                    ("heart_rate", hr_val, "bpm"),
                    ("spo2", spo2_val, "%"),
                    ("respiratory_rate", rr_val, "breaths/min"),
                    ("blood_glucose", glu_val, "mg/dL"),
                    ("body_temp", temp_val, "°C"),
                    ("bmi", bmi_val, "kg/m²"),
                    ("creatinine", creat_val, "mg/dL"),
                ]

                for m_type, val, unit in measurements_pool:
                    is_valid, status, msg = validate_measurement_value(m_type, val)
                    m_id = f"M-{uuid.uuid4().hex[:12]}"
                    meas = Measurement(
                        measurement_id=m_id,
                        patient_id=patient.patient_id,
                        visit_id=v_id,
                        measurement_date=visit_dt,
                        measure_type=m_type,
                        value=round(val, 2),
                        unit=unit,
                        is_valid_range=is_valid,
                        validation_status=status
                    )
                    db.add(meas)
                    total_measurements += 1
                    
                    # Store latest valid measurement for indicator calculation
                    if is_valid:
                        patient_latest_measures[m_type] = round(val, 2)

            # Evaluate transparent rule-based indicators for this patient based on latest measurement profile
            triggered_rules = evaluate_patient_indicators(patient_latest_measures)
            for rule in triggered_rules:
                ind_id = f"IND-{patient.patient_id}-{rule['rule_code']}"
                indicator = RiskIndicator(
                    indicator_id=ind_id,
                    patient_id=patient.patient_id,
                    rule_code=rule["rule_code"],
                    indicator_value=rule["indicator_value"],
                    indicator_category=rule["indicator_category"],
                    rationale=rule["rationale"],
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(indicator)

        db.commit()
        print(f"Synthetic dataset initialized: {num_patients} patients, {total_visits} visits, {total_measurements} measurements.")
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_synthetic_data()
