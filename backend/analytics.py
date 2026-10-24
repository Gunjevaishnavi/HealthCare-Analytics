"""
Healthcare Analytics Engine: Pandas & NumPy Processing
------------------------------------------------------
Performs operational aggregations, statistical summaries, data cleaning,
and demographic / indicator cross-tabulations on synthetic health records.
Non-clinical statistical analysis only.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.database import SessionLocal, Patient, Visit, Measurement, RiskIndicator, Department
from backend.rules_engine import MEASUREMENT_SPECS, RULE_DEFINITIONS


def get_operational_analytics_report(db: Session = None) -> Dict[str, Any]:
    """
    Computes an extensive operational analytics report summarizing department admissions,
    demographics, vital measurement distributions, and indicator triggers.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Load tables into Pandas DataFrames for high-performance vectorized operations
        patients_query = db.query(Patient).statement
        visits_query = db.query(Visit).statement
        measurements_query = db.query(Measurement).statement
        indicators_query = db.query(RiskIndicator).statement
        departments_query = db.query(Department).statement

        df_patients = pd.read_sql(patients_query, db.bind)
        df_visits = pd.read_sql(visits_query, db.bind)
        df_measurements = pd.read_sql(measurements_query, db.bind)
        df_indicators = pd.read_sql(indicators_query, db.bind)
        df_depts = pd.read_sql(departments_query, db.bind)

        # 1. High-Level KPI Summary
        total_patients = len(df_patients)
        total_visits = len(df_visits)
        total_measurements = len(df_measurements)
        total_indicators = len(df_indicators)

        # 2. Demographics & Cohort Analysis (Pandas Grouping)
        age_dist = df_patients["age_band"].value_counts().to_dict()
        gender_dist = df_patients["gender"].value_counts().to_dict()
        region_dist = df_patients["residence_region"].value_counts().to_dict()
        
        # Chronic condition rate by age band
        chronic_by_age = df_patients.groupby("age_band")["chronic_condition_flag"].agg(["count", "mean"]).reset_index()
        chronic_summary = [
            {
                "age_band": row["age_band"],
                "total": int(row["count"]),
                "chronic_pct": round(float(row["mean"]) * 100, 1)
            }
            for _, row in chronic_by_age.iterrows()
        ]

        # 3. Department Admissions & Workload (Pandas & NumPy)
        # Merge visits with departments
        df_visits["visit_date"] = pd.to_datetime(df_visits["visit_date"])
        df_visits["discharge_date"] = pd.to_datetime(df_visits["discharge_date"])
        df_visits["los_hours"] = (df_visits["discharge_date"] - df_visits["visit_date"]).dt.total_seconds() / 3600.0

        visits_dept = df_visits.merge(df_depts, on="department_id", how="left")
        
        dept_summary_df = visits_dept.groupby(["department_id", "department_name"]).agg(
            total_admissions=("visit_id", "count"),
            avg_los_hours=("los_hours", "mean"),
            median_los_hours=("los_hours", "median"),
            emergency_count=("admission_type", lambda s: (s == "Emergency").sum()),
            elective_count=("admission_type", lambda s: (s == "Elective").sum()),
            urgent_count=("admission_type", lambda s: (s == "Urgent").sum()),
            routine_count=("admission_type", lambda s: (s == "Routine Outpatient").sum())
        ).reset_index()

        dept_workload = []
        for _, row in dept_summary_df.iterrows():
            dept_workload.append({
                "department_id": row["department_id"],
                "department_name": row["department_name"],
                "total_admissions": int(row["total_admissions"]),
                "avg_los_hours": round(float(row["avg_los_hours"]), 1) if not pd.isna(row["avg_los_hours"]) else 0.0,
                "median_los_hours": round(float(row["median_los_hours"]), 1) if not pd.isna(row["median_los_hours"]) else 0.0,
                "emergency_count": int(row["emergency_count"]),
                "elective_count": int(row["elective_count"]),
                "urgent_count": int(row["urgent_count"]),
                "routine_count": int(row["routine_count"]),
            })

        # 4. NumPy Statistical Summaries on Health Measurements
        measurement_stats = {}
        for m_type in df_measurements["measure_type"].unique():
            subset = df_measurements[df_measurements["measure_type"] == m_type]["value"].dropna().to_numpy()
            if len(subset) > 0:
                spec = MEASUREMENT_SPECS.get(m_type, {})
                q25, q50, q75 = np.percentile(subset, [25, 50, 75])
                iqr = q75 - q25
                p05, p95 = np.percentile(subset, [5, 95])
                
                # Validation status counts
                status_series = df_measurements[df_measurements["measure_type"] == m_type]["validation_status"].value_counts().to_dict()

                measurement_stats[m_type] = {
                    "display_name": spec.get("display_name", m_type),
                    "unit": spec.get("unit", ""),
                    "count": int(len(subset)),
                    "mean": round(float(np.mean(subset)), 2),
                    "std": round(float(np.std(subset)), 2),
                    "median": round(float(q50), 2),
                    "iqr": round(float(iqr), 2),
                    "p25": round(float(q25), 2),
                    "p75": round(float(q75), 2),
                    "p05": round(float(p05), 2),
                    "p95": round(float(p95), 2),
                    "min": round(float(np.min(subset)), 2),
                    "max": round(float(np.max(subset)), 2),
                    "validation_breakdown": status_series
                }

        # 5. Risk Indicator Counts and Distributions
        ind_counts = df_indicators["rule_code"].value_counts().to_dict()
        
        # Merge indicators with patients to cross-tabulate by age band
        merged_ind = df_indicators.merge(df_patients[["patient_id", "age_band"]], on="patient_id", how="left")
        crosstab_df = pd.crosstab(merged_ind["age_band"], merged_ind["rule_code"]).fillna(0)
        
        crosstab_list = []
        for age_band, row in crosstab_df.iterrows():
            item = {"age_band": age_band}
            for code in ["R-VIT-01", "R-GLU-02", "R-RES-03", "R-REN-04", "R-COM-05"]:
                item[code] = int(row.get(code, 0))
            crosstab_list.append(item)

        # Multi-indicator patients (% of cohort with >= 2 indicators)
        patient_ind_counts = df_indicators.groupby("patient_id")["rule_code"].count()
        multi_indicator_patients = int((patient_ind_counts >= 2).sum())
        multi_indicator_pct = round((multi_indicator_patients / max(total_patients, 1)) * 100, 1)

        # 6. Weekly Visit Trends (Time-series)
        df_visits["week_label"] = df_visits["visit_date"].dt.strftime("%Y-W%U")
        weekly_admissions = df_visits.groupby("week_label")["visit_id"].count().reset_index()
        weekly_trends = [
            {"week": row["week_label"], "visits": int(row["visit_id"])}
            for _, row in weekly_admissions.sort_values("week_label").iterrows()
        ]

        return {
            "summary": {
                "total_patients": total_patients,
                "total_visits": total_visits,
                "total_measurements": total_measurements,
                "total_indicators_flagged": total_indicators,
                "multi_indicator_patients": multi_indicator_patients,
                "multi_indicator_pct": multi_indicator_pct
            },
            "demographics": {
                "age_distribution": age_dist,
                "gender_distribution": gender_dist,
                "region_distribution": region_dist,
                "chronic_by_age": chronic_summary
            },
            "departments": dept_workload,
            "measurement_statistics": measurement_stats,
            "indicators": {
                "rule_counts": ind_counts,
                "rule_definitions": RULE_DEFINITIONS,
                "crosstab_by_age": crosstab_list
            },
            "trends": {
                "weekly_visits": weekly_trends
            }
        }
    finally:
        if close_db:
            db.close()
