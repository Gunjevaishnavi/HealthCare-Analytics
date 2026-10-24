"""
Analytics & Machine Learning REST Routes
-----------------------------------------
Delivers NumPy statistical summaries, Pandas operational analytics,
and Scikit-Learn educational model evaluations.
"""

from flask import Blueprint, jsonify, request
from backend.auth import require_api_key
from backend.analytics import get_operational_analytics_report
from backend.visualization import generate_all_charts
from backend.ml_experiment import run_educational_ml_experiment
from backend.config import Config

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1")


@analytics_bp.route("/analytics/operational-summary", methods=["GET"])
@require_api_key
def operational_summary_api():
    """Full operational analytics payload with department workload and vital stats."""
    report = get_operational_analytics_report()
    report["disclaimer"] = Config.MANDATORY_LIMITATIONS_STATEMENT
    return jsonify(report), 200


@analytics_bp.route("/analytics/department-trends", methods=["GET"])
@require_api_key
def department_trends_api():
    """Admissions and stay duration trends per department."""
    report = get_operational_analytics_report()
    return jsonify({
        "status": "success",
        "departments": report["departments"],
        "weekly_admissions": report["trends"]["weekly_visits"]
    }), 200


@analytics_bp.route("/analytics/measurement-stats", methods=["GET"])
@require_api_key
def measurement_stats_api():
    """NumPy statistical distributions across physiological parameters."""
    report = get_operational_analytics_report()
    return jsonify({
        "status": "success",
        "measurement_statistics": report["measurement_statistics"]
    }), 200


@analytics_bp.route("/analytics/indicator-distribution", methods=["GET"])
@require_api_key
def indicator_distribution_api():
    """Indicator trigger counts and demographic cross-tabulation."""
    report = get_operational_analytics_report()
    return jsonify({
        "status": "success",
        "rule_counts": report["indicators"]["rule_counts"],
        "crosstab_by_age": report["indicators"]["crosstab_by_age"]
    }), 200


@analytics_bp.route("/analytics/regenerate-charts", methods=["POST"])
@require_api_key
def regenerate_charts_api():
    """Reruns Matplotlib headless plotting to update static PNG charts."""
    try:
        charts = generate_all_charts()
        return jsonify({
            "status": "success",
            "message": "Matplotlib operational charts recomputed and updated.",
            "charts": charts
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@analytics_bp.route("/ml/educational-evaluation", methods=["GET", "POST"])
@require_api_key
def ml_evaluation_api():
    """Runs or fetches the scikit-learn educational classification benchmark."""
    try:
        result = run_educational_ml_experiment()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
