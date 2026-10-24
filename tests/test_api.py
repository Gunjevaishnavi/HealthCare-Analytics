"""
Integration Tests: REST API Endpoints & Access Control
"""

import unittest
import json
from backend.app import create_app
from backend.synthetic_data import seed_synthetic_data


class TestApiEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        seed_synthetic_data(num_patients=30)
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.headers = {"X-API-Key": "health-demo-key-2026", "Content-Type": "application/json"}

    def test_unauthorized_access(self):
        # Without API Key or session -> 401
        res = self.client.get("/api/v1/patients")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertIn("error", data)

    def test_authorized_get_patients(self):
        res = self.client.get("/api/v1/patients?limit=10", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(len(data["data"]), 0)
        self.assertIn("disclaimer", data)

    def test_post_patient_and_get_detail(self):
        pat_payload = {
            "patient_id": "PAT-TEST-9999",
            "age_band": "51-65",
            "gender": "Female",
            "ethnicity_code": "ETH_A1",
            "chronic_condition_flag": True
        }
        res_post = self.client.post("/api/v1/patients", data=json.dumps(pat_payload), headers=self.headers)
        self.assertIn(res_post.status_code, (201, 409)) # 201 or 409 if already exists

        # Retrieve detail
        res_get = self.client.get("/api/v1/patients/PAT-TEST-9999", headers=self.headers)
        self.assertEqual(res_get.status_code, 200)
        data = res_get.get_json()
        self.assertEqual(data["patient"]["patient_id"], "PAT-TEST-9999")

    def test_get_visits(self):
        res = self.client.get("/api/v1/visits?limit=5", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreater(len(data["data"]), 0)

    def test_measurement_validation_endpoint(self):
        # Public ad-hoc range validation
        payload = {"measure_type": "blood_glucose", "value": 150.0}
        res = self.client.post("/api/v1/measurements/validate", data=json.dumps(payload), headers={"Content-Type": "application/json"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["validation_status"], "OUT_OF_RANGE_HIGH")
        self.assertTrue(data["is_valid_range"])

    def test_operational_summary_analytics(self):
        res = self.client.get("/api/v1/analytics/operational-summary", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("summary", data)
        self.assertIn("departments", data)
        self.assertIn("measurement_statistics", data)
        self.assertIn("disclaimer", data)

    def test_ml_educational_evaluation_endpoint(self):
        res = self.client.get("/api/v1/ml/educational-evaluation", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("models", data)
        self.assertIn("logistic_regression", data["models"])
        self.assertIn("random_forest", data["models"])
        self.assertIn("disclaimer", data)


if __name__ == "__main__":
    unittest.main()
