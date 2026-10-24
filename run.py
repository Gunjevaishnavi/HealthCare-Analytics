#!/usr/bin/env python3
"""
Application Entry Point: Project 23 Healthcare Analytics System
---------------------------------------------------------------
Usage:
    python run.py
"""

import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.config import Config
from backend.synthetic_data import seed_synthetic_data
from backend.visualization import generate_all_charts
from backend.app import create_app


def main():
    print("=" * 75)
    print(" PROJECT 23: HEALTHCARE ANALYTICS & PATIENT RISK INDICATOR SYSTEM")
    print("=" * 75)
    print("[1/3] Checking synthetic database and seeding records if needed...")
    seed_synthetic_data(num_patients=200)

    print("[2/3] Rendering headless Matplotlib operational charts...")
    chart_dir = Config.CHARTS_DIR
    if not os.path.exists(os.path.join(chart_dir, "dept_admissions_trend.png")):
        generate_all_charts()
    else:
        print("Charts verified in:", chart_dir)

    print("[3/3] Starting Healthcare Analytics Web Server...")
    print("\n" + "*" * 75)
    print("  >>> APPLICATION RUNNING: http://127.0.0.1:5050 <<<")
    print("*" * 75)
    print("  Demo Web Login:  Username: analyst  |  Password: Password123!")
    print("  REST API Key:    health-demo-key-2026 (Header: 'X-API-Key')")
    print("  Boundaries:      Strictly Educational & Non-Clinical Analytics")
    print("*" * 75 + "\n")

    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=False)


if __name__ == "__main__":
    main()
