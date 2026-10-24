"""
Unit Tests: Physiological Measurement Validation & Rule Engine
"""

import unittest
from backend.rules_engine import validate_measurement_value, evaluate_patient_indicators


class TestRulesEngine(unittest.TestCase):

    def test_normal_measurement_validation(self):
        # Systolic BP 115 is within normal range [90, 120]
        is_valid, status, msg = validate_measurement_value("systolic_bp", 115.0)
        self.assertTrue(is_valid)
        self.assertEqual(status, "VALID")

        # Heart rate 72 is normal [60, 100]
        is_valid, status, msg = validate_measurement_value("heart_rate", 72.0)
        self.assertTrue(is_valid)
        self.assertEqual(status, "VALID")

    def test_out_of_range_high_validation(self):
        # Systolic BP 145 is out of range high (> 120) but biologically plausible (< 260)
        is_valid, status, msg = validate_measurement_value("systolic_bp", 145.0)
        self.assertTrue(is_valid)
        self.assertEqual(status, "OUT_OF_RANGE_HIGH")

        # Fasting glucose 135 is out of range high (> 99)
        is_valid, status, msg = validate_measurement_value("blood_glucose", 135.0)
        self.assertTrue(is_valid)
        self.assertEqual(status, "OUT_OF_RANGE_HIGH")

    def test_out_of_range_low_validation(self):
        # Heart rate 52 is bradycardic (< 60) but plausible (> 30)
        is_valid, status, msg = validate_measurement_value("heart_rate", 52.0)
        self.assertTrue(is_valid)
        self.assertEqual(status, "OUT_OF_RANGE_LOW")

    def test_implausible_measurement_validation(self):
        # Systolic BP 290 is implausible (> 260)
        is_valid, status, msg = validate_measurement_value("systolic_bp", 290.0)
        self.assertFalse(is_valid)
        self.assertEqual(status, "IMPLAUSIBLE_VALUE")

        # SpO2 40% is implausibly low (< 50)
        is_valid, status, msg = validate_measurement_value("spo2", 40.0)
        self.assertFalse(is_valid)
        self.assertEqual(status, "IMPLAUSIBLE_VALUE")

    def test_cardiovascular_rule_trigger(self):
        # SBP >= 140 triggers R-VIT-01
        measures = {"systolic_bp": 148.0, "heart_rate": 75.0}
        indicators = evaluate_patient_indicators(measures)
        rule_codes = [i["rule_code"] for i in indicators]
        self.assertIn("R-VIT-01", rule_codes)

    def test_metabolic_rule_trigger(self):
        # Glucose >= 126 triggers R-GLU-02
        measures = {"blood_glucose": 130.0}
        indicators = evaluate_patient_indicators(measures)
        rule_codes = [i["rule_code"] for i in indicators]
        self.assertIn("R-GLU-02", rule_codes)

        # Glucose 105 and BMI 32 triggers R-GLU-02
        measures_combo = {"blood_glucose": 105.0, "bmi": 32.5}
        indicators_combo = evaluate_patient_indicators(measures_combo)
        rule_codes_combo = [i["rule_code"] for i in indicators_combo]
        self.assertIn("R-GLU-02", rule_codes_combo)

    def test_multisystem_composite_rule_trigger(self):
        # High BP and Low SpO2 triggers R-VIT-01, R-RES-03, and R-COM-05
        measures = {
            "systolic_bp": 150.0,
            "spo2": 90.0,
            "respiratory_rate": 26.0
        }
        indicators = evaluate_patient_indicators(measures)
        rule_codes = [i["rule_code"] for i in indicators]
        self.assertIn("R-VIT-01", rule_codes)
        self.assertIn("R-RES-03", rule_codes)
        self.assertIn("R-COM-05", rule_codes)


if __name__ == "__main__":
    unittest.main()
