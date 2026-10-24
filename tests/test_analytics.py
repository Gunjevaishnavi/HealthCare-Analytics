"""
Unit Tests: Pandas Operational Processing & NumPy Statistics
"""

import unittest
from backend.analytics import get_operational_analytics_report
from backend.synthetic_data import seed_synthetic_data


class TestAnalyticsEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        seed_synthetic_data(num_patients=30)
        cls.report = get_operational_analytics_report()

    def test_summary_keys(self):
        summary = self.report["summary"]
        self.assertGreater(summary["total_patients"], 0)
        self.assertGreater(summary["total_visits"], 0)
        self.assertGreater(summary["total_measurements"], 0)
        self.assertIn("multi_indicator_pct", summary)

    def test_department_workload_metrics(self):
        depts = self.report["departments"]
        self.assertGreater(len(depts), 0)
        for d in depts:
            self.assertIn("department_id", d)
            self.assertIn("total_admissions", d)
            self.assertIn("avg_los_hours", d)

    def test_numpy_statistical_summaries(self):
        stats = self.report["measurement_statistics"]
        self.assertIn("systolic_bp", stats)
        sbp = stats["systolic_bp"]
        self.assertIn("mean", sbp)
        self.assertIn("median", sbp)
        self.assertIn("std", sbp)
        self.assertIn("iqr", sbp)
        self.assertIn("p05", sbp)
        self.assertIn("p95", sbp)
        # Check statistical sanity: min <= p05 <= median <= p95 <= max
        self.assertLessEqual(sbp["min"], sbp["p05"])
        self.assertLessEqual(sbp["p05"], sbp["median"])
        self.assertLessEqual(sbp["median"], sbp["p95"])
        self.assertLessEqual(sbp["p95"], sbp["max"])


if __name__ == "__main__":
    unittest.main()
