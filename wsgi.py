"""
Production WSGI Entry Point for Cloud Deployment (Render, Railway, Heroku, etc.)
---------------------------------------------------------------------------------
Usage:
    gunicorn wsgi:app
"""

import os
import sys

# Ensure project root is in python path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from backend.config import Config
from backend.synthetic_data import seed_synthetic_data
from backend.visualization import generate_all_charts
from backend.app import create_app

# Automatically initialize database and charts on startup
seed_synthetic_data(num_patients=200)

chart_dir = Config.CHARTS_DIR
if not os.path.exists(os.path.join(chart_dir, "dept_admissions_trend.png")):
    generate_all_charts()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)
