"""
Healthcare Measurement Range Validation & Transparent Rule-Based Indicators
----------------------------------------------------------------------------
EDUCATIONAL PURPOSES ONLY:
The ranges and indicators defined in this module represent illustrative sample
assumptions based on generalized physiological textbooks and public health guidelines.
They are NOT intended to provide medical diagnoses, treatment instructions, or
clinical triage decisions.
"""

from typing import Dict, Any, Tuple, List
import datetime

# Documented Physiological Assumptions for Synthetic Measurement Validation
MEASUREMENT_SPECS: Dict[str, Dict[str, Any]] = {
    "systolic_bp": {
        "display_name": "Systolic Blood Pressure",
        "unit": "mmHg",
        "plausible_min": 50.0,
        "plausible_max": 260.0,
        "normal_min": 90.0,
        "normal_max": 120.0,
        "elevated_threshold": 140.0,
        "assumption_notes": "Assumes resting adult measurement. Values <50 or >260 mmHg indicate sensor malfunction or extreme artifact."
    },
    "diastolic_bp": {
        "display_name": "Diastolic Blood Pressure",
        "unit": "mmHg",
        "plausible_min": 30.0,
        "plausible_max": 150.0,
        "normal_min": 60.0,
        "normal_max": 80.0,
        "elevated_threshold": 90.0,
        "assumption_notes": "Assumes standard automated cuff. Values <30 or >150 mmHg flagged as implausible sample recording."
    },
    "heart_rate": {
        "display_name": "Heart Rate",
        "unit": "bpm",
        "plausible_min": 30.0,
        "plausible_max": 220.0,
        "normal_min": 60.0,
        "normal_max": 100.0,
        "elevated_threshold": 105.0,
        "assumption_notes": "Adult resting pulse. <60 bpm indicates bradycardia trend, >100 bpm indicates tachycardia trend."
    },
    "respiratory_rate": {
        "display_name": "Respiratory Rate",
        "unit": "breaths/min",
        "plausible_min": 6.0,
        "plausible_max": 60.0,
        "normal_min": 12.0,
        "normal_max": 20.0,
        "elevated_threshold": 24.0,
        "assumption_notes": "Spontaneous breathing rate in rested state. >24 bpm represents potential tachypneic pattern."
    },
    "body_temp": {
        "display_name": "Body Temperature",
        "unit": "°C",
        "plausible_min": 32.0,
        "plausible_max": 43.0,
        "normal_min": 36.1,
        "normal_max": 37.2,
        "elevated_threshold": 38.0,
        "assumption_notes": "Core or tympanic temperature. <35.5 C hypothermia suspicion; >38.0 C febrile pattern."
    },
    "spo2": {
        "display_name": "Oxygen Saturation (SpO2)",
        "unit": "%",
        "plausible_min": 50.0,
        "plausible_max": 100.0,
        "normal_min": 95.0,
        "normal_max": 100.0,
        "low_threshold": 92.0,
        "assumption_notes": "Pulse oximetry reading on ambient air. <=92% warrants operational review for supplemental oxygen check."
    },
    "blood_glucose": {
        "display_name": "Fasting Blood Glucose",
        "unit": "mg/dL",
        "plausible_min": 30.0,
        "plausible_max": 600.0,
        "normal_min": 70.0,
        "normal_max": 99.0,
        "elevated_threshold": 126.0,
        "assumption_notes": "Assumes standard overnight fasting state. >=126 mg/dL flagged as illustrative glycemic indicator."
    },
    "bmi": {
        "display_name": "Body Mass Index",
        "unit": "kg/m²",
        "plausible_min": 12.0,
        "plausible_max": 75.0,
        "normal_min": 18.5,
        "normal_max": 24.9,
        "elevated_threshold": 30.0,
        "assumption_notes": "Calculated weight/height^2. >=30.0 classified as obesity class benchmark."
    },
    "creatinine": {
        "display_name": "Serum Creatinine",
        "unit": "mg/dL",
        "plausible_min": 0.2,
        "plausible_max": 18.0,
        "normal_min": 0.6,
        "normal_max": 1.2,
        "elevated_threshold": 1.5,
        "assumption_notes": "Renal metabolic filtration marker. >=1.5 mg/dL flagged for potential clearance review."
    }
}

# Documented Transparent Rule Definitions
RULE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "R-VIT-01": {
        "name": "Cardiovascular Vital Stress Indicator",
        "category": "Cardiovascular",
        "logic_description": "Triggers if Systolic BP >= 140 mmHg OR Heart Rate >= 105 bpm.",
        "sample_thresholds": {"systolic_bp": ">= 140 mmHg", "heart_rate": ">= 105 bpm"},
        "rationale": "Identifies elevated hemodynamic stress or autonomic activation for observational cohort grouping.",
        "severity": "Moderate"
    },
    "R-GLU-02": {
        "name": "Metabolic Glycemic Screening Indicator",
        "category": "Metabolic",
        "logic_description": "Triggers if Fasting Blood Glucose >= 126 mg/dL OR (Glucose >= 100 mg/dL AND BMI >= 30.0 kg/m²).",
        "sample_thresholds": {"blood_glucose": ">= 126 mg/dL", "combo": "Glucose >= 100 AND BMI >= 30"},
        "rationale": "Flags prospective metabolic syndrome patterns in educational population risk simulations.",
        "severity": "Moderate"
    },
    "R-RES-03": {
        "name": "Respiratory Compromise Watch Indicator",
        "category": "Respiratory",
        "logic_description": "Triggers if SpO2 <= 92% OR Respiratory Rate >= 24 breaths/min.",
        "sample_thresholds": {"spo2": "<= 92%", "respiratory_rate": ">= 24 breaths/min"},
        "rationale": "Captures ventilatory stress and potential hypoxemia patterns in synthetic acute cohorts.",
        "severity": "High"
    },
    "R-REN-04": {
        "name": "Renal Clearance Screening Indicator",
        "category": "Renal",
        "logic_description": "Triggers if Serum Creatinine >= 1.5 mg/dL.",
        "sample_thresholds": {"creatinine": ">= 1.5 mg/dL"},
        "rationale": "Flags synthetic renal filtration abnormalities for non-clinical observational analytics.",
        "severity": "Moderate"
    },
    "R-COM-05": {
        "name": "Multisystem Composite Watch Indicator",
        "category": "Composite",
        "logic_description": "Triggers when 2 or more of (R-VIT-01, R-GLU-02, R-RES-03, R-REN-04) are active.",
        "sample_thresholds": {"min_indicators_active": 2},
        "rationale": "Highlights multisystem operational vulnerability across departments for hospital resource planning.",
        "severity": "High"
    }
}


def validate_measurement_value(measure_type: str, value: float) -> Tuple[bool, str, str]:
    """
    Validates a measurement against documented physiological sample ranges.
    Returns: (is_valid_range, validation_status, message)
    """
    spec = MEASUREMENT_SPECS.get(measure_type)
    if not spec:
        return True, "UNVALIDATED_TYPE", f"Measure type '{measure_type}' has no preset validation rules."

    # 1. Check physical/physiological plausibility
    if value < spec["plausible_min"] or value > spec["plausible_max"]:
        return (
            False,
            "IMPLAUSIBLE_VALUE",
            f"Value {value} {spec['unit']} lies outside plausible biological limit [{spec['plausible_min']}, {spec['plausible_max']}]."
        )

    # 2. Check clinical sample assumptions
    if value < spec["normal_min"]:
        return (
            True,
            "OUT_OF_RANGE_LOW",
            f"Value {value} {spec['unit']} is below documented reference minimum ({spec['normal_min']} {spec['unit']})."
        )
    elif value > spec["normal_max"]:
        return (
            True,
            "OUT_OF_RANGE_HIGH",
            f"Value {value} {spec['unit']} exceeds documented reference maximum ({spec['normal_max']} {spec['unit']})."
        )

    return True, "VALID", f"Value {value} {spec['unit']} is within standard reference interval."


def evaluate_patient_indicators(measurements_dict: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Computes transparent rule-based indicators for a patient given their latest measurements.
    measurements_dict: e.g. {'systolic_bp': 145, 'heart_rate': 110, ...}
    Returns a list of triggered risk indicator objects.
    """
    triggered_rules = []
    single_rule_triggers = set()

    # Rule 1: R-VIT-01
    sbp = measurements_dict.get("systolic_bp")
    hr = measurements_dict.get("heart_rate")
    if (sbp is not None and sbp >= 140.0) or (hr is not None and hr >= 105.0):
        reasons = []
        if sbp is not None and sbp >= 140.0:
            reasons.append(f"Systolic BP ({sbp} mmHg >= 140 mmHg)")
        if hr is not None and hr >= 105.0:
            reasons.append(f"Heart Rate ({hr} bpm >= 105 bpm)")
        
        triggered_rules.append({
            "rule_code": "R-VIT-01",
            "indicator_value": 1.0,
            "indicator_category": "Cardiovascular",
            "rationale": f"Flagged due to: {', '.join(reasons)}. Documented hemodynamic threshold exceeded."
        })
        single_rule_triggers.add("R-VIT-01")

    # Rule 2: R-GLU-02
    glucose = measurements_dict.get("blood_glucose")
    bmi = measurements_dict.get("bmi")
    if glucose is not None:
        if glucose >= 126.0:
            triggered_rules.append({
                "rule_code": "R-GLU-02",
                "indicator_value": 1.0,
                "indicator_category": "Metabolic",
                "rationale": f"Fasting glucose {glucose} mg/dL exceeds hyperglycemic benchmark (>= 126 mg/dL)."
            })
            single_rule_triggers.add("R-GLU-02")
        elif glucose >= 100.0 and (bmi is not None and bmi >= 30.0):
            triggered_rules.append({
                "rule_code": "R-GLU-02",
                "indicator_value": 0.85,
                "indicator_category": "Metabolic",
                "rationale": f"Impaired fasting glucose ({glucose} mg/dL) combined with elevated BMI ({bmi} kg/m² >= 30)."
            })
            single_rule_triggers.add("R-GLU-02")

    # Rule 3: R-RES-03
    spo2 = measurements_dict.get("spo2")
    rr = measurements_dict.get("respiratory_rate")
    if (spo2 is not None and spo2 <= 92.0) or (rr is not None and rr >= 24.0):
        reasons = []
        if spo2 is not None and spo2 <= 92.0:
            reasons.append(f"Oxygen Saturation ({spo2}% <= 92%)")
        if rr is not None and rr >= 24.0:
            reasons.append(f"Respiratory Rate ({rr} breaths/min >= 24)")
        
        triggered_rules.append({
            "rule_code": "R-RES-03",
            "indicator_value": 1.0,
            "indicator_category": "Respiratory",
            "rationale": f"Ventilatory compromise pattern: {', '.join(reasons)}."
        })
        single_rule_triggers.add("R-RES-03")

    # Rule 4: R-REN-04
    creat = measurements_dict.get("creatinine")
    if creat is not None and creat >= 1.5:
        triggered_rules.append({
            "rule_code": "R-REN-04",
            "indicator_value": 1.0,
            "indicator_category": "Renal",
            "rationale": f"Serum Creatinine {creat} mg/dL is at or above clearance screening cutoff (>= 1.5 mg/dL)."
        })
        single_rule_triggers.add("R-REN-04")

    # Rule 5: R-COM-05 Composite
    if len(single_rule_triggers) >= 2:
        triggered_rules.append({
            "rule_code": "R-COM-05",
            "indicator_value": float(len(single_rule_triggers)),
            "indicator_category": "Composite",
            "rationale": f"Multisystem review flag: {len(single_rule_triggers)} independent risk indicators active ({', '.join(sorted(single_rule_triggers))})."
        })

    return triggered_rules
