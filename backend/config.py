import os

# Prevent Matplotlib cache permission warnings on macOS/sandboxes
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.makedirs("/tmp/matplotlib", exist_ok=True)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHARTS_DIR = os.path.join(BASE_DIR, "static", "charts")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    CHARTS_DIR = CHARTS_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "healthcare-analytics-secret-key-2026")
    
    # SQLite by default; supports MySQL if DATABASE_URL is set (e.g., mysql+pymysql://user:pass@host/db)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", 
        f"sqlite:///{os.path.join(DATA_DIR, 'healthcare.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Access Restriction: valid API Keys and default credentials
    VALID_API_KEYS = {
        "health-demo-key-2026": "Healthcare Analyst (Demo)",
        "admin-key-sec-99": "System Administrator",
        "auditor-key-eval-12": "Compliance Auditor"
    }
    
    DEFAULT_USER = {
        "username": "analyst",
        "password": "Password123!",
        "role": "Healthcare Data Analyst"
    }
    
    # Official Project Boundaries & Mandatory Limitations Statement
    MANDATORY_LIMITATIONS_STATEMENT = (
        "EDUCATIONAL HEALTHCARE ANALYTICS SYSTEM ONLY. "
        "All data processed within this system is synthetic or fully de-identified. "
        "The computed indicators, operational summaries, and machine learning models "
        "are strictly illustrative statistical indicators and DO NOT constitute medical advice, "
        "clinical diagnoses, prognostic determinations, or treatment recommendations. "
        "This software MUST NOT be used for real-world patient triage, bedside decision-making, "
        "or clinical management."
    )
