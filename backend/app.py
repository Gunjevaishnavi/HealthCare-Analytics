"""
Main Healthcare Analytics Flask Application
--------------------------------------------
Combines Web UI Dashboard with REST APIs, Analytics Pipelines, and Access Restriction.
"""

import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify

from backend.config import Config
from backend.database import init_db, SessionLocal, Patient, Visit, Measurement, RiskIndicator, Department
from backend.auth import require_auth
from backend.routes.auth_routes import auth_bp
from backend.routes.api_routes import api_bp
from backend.routes.analytics_routes import analytics_bp
from backend.analytics import get_operational_analytics_report
from backend.rules_engine import MEASUREMENT_SPECS, RULE_DEFINITIONS
from backend.ml_experiment import run_educational_ml_experiment


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(Config.BASE_DIR, "templates"),
        static_folder=os.path.join(Config.BASE_DIR, "static")
    )
    app.config.from_object(Config)

    # Initialize DB tables
    init_db()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analytics_bp)

    @app.context_processor
    def inject_global_template_data():
        return {
            "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT,
            "current_user": session.get("username", None),
            "current_role": session.get("role", None),
            "is_auth": session.get("authenticated", False),
            "valid_demo_key": "health-demo-key-2026"
        }

    # ---------------- Web UI Dashboard Views ---------------- #

    @app.route("/")
    @require_auth
    def dashboard_view():
        """Executive KPI overview with department admissions and indicator breakdowns."""
        db = SessionLocal()
        try:
            report = get_operational_analytics_report(db)
            recent_indicators = db.query(RiskIndicator).order_by(RiskIndicator.created_at.desc()).limit(8).all()
            recent_visits = db.query(Visit).order_by(Visit.visit_date.desc()).limit(8).all()
            
            return render_template(
                "index.html",
                report=report,
                recent_indicators=[i.to_dict() for i in recent_indicators],
                recent_visits=[v.to_dict() for v in recent_visits],
                measurement_specs=MEASUREMENT_SPECS,
                rule_definitions=RULE_DEFINITIONS
            )
        finally:
            db.close()

    @app.route("/patients")
    @require_auth
    def patients_view():
        """Patient cohort explorer with age band and chronic condition filtering."""
        db = SessionLocal()
        try:
            age_band = request.args.get("age_band", "")
            chronic = request.args.get("chronic", "")
            search = request.args.get("search", "")

            query = db.query(Patient)
            if age_band:
                query = query.filter(Patient.age_band == age_band)
            if chronic:
                query = query.filter(Patient.chronic_condition_flag == (chronic.lower() == "true"))
            if search:
                query = query.filter(Patient.patient_id.like(f"%{search}%"))

            patients = query.order_by(Patient.patient_id).limit(100).all()
            
            return render_template(
                "patients.html",
                patients=[p.to_dict() for p in patients],
                total_displayed=len(patients),
                selected_age=age_band,
                selected_chronic=chronic,
                search_term=search
            )
        finally:
            db.close()

    @app.route("/visits")
    @require_auth
    def visits_view():
        """Clinical encounters and department admissions table."""
        db = SessionLocal()
        try:
            dept_filter = request.args.get("department_id", "")
            adm_filter = request.args.get("admission_type", "")

            query = db.query(Visit)
            if dept_filter:
                query = query.filter(Visit.department_id == dept_filter)
            if adm_filter:
                query = query.filter(Visit.admission_type == adm_filter)

            visits = query.order_by(Visit.visit_date.desc()).limit(100).all()
            departments = db.query(Department).all()

            return render_template(
                "visits.html",
                visits=[v.to_dict() for v in visits],
                departments=[d.to_dict() for d in departments],
                selected_dept=dept_filter,
                selected_adm=adm_filter
            )
        finally:
            db.close()

    @app.route("/measurements")
    @require_auth
    def measurements_view():
        """Measurement logs with validation status and interactive range test tool."""
        db = SessionLocal()
        try:
            m_type = request.args.get("measure_type", "")
            status = request.args.get("status", "")

            query = db.query(Measurement)
            if m_type:
                query = query.filter(Measurement.measure_type == m_type)
            if status:
                query = query.filter(Measurement.validation_status == status)

            measurements = query.order_by(Measurement.measurement_date.desc()).limit(120).all()

            return render_template(
                "measurements.html",
                measurements=[m.to_dict() for m in measurements],
                specs=MEASUREMENT_SPECS,
                selected_type=m_type,
                selected_status=status
            )
        finally:
            db.close()

    @app.route("/indicators")
    @require_auth
    def indicators_view():
        """Transparent rule-based risk indicators, documented assumptions, and trigger log."""
        db = SessionLocal()
        try:
            rule_code = request.args.get("rule_code", "")
            query = db.query(RiskIndicator)
            if rule_code:
                query = query.filter(RiskIndicator.rule_code == rule_code)

            indicators = query.order_by(RiskIndicator.created_at.desc()).limit(120).all()

            return render_template(
                "indicators.html",
                indicators=[i.to_dict() for i in indicators],
                rule_definitions=RULE_DEFINITIONS,
                selected_rule=rule_code
            )
        finally:
            db.close()

    @app.route("/operational-report")
    @require_auth
    def operational_report_view():
        """Comprehensive operational analytics report with Matplotlib charts."""
        db = SessionLocal()
        try:
            report = get_operational_analytics_report(db)
            return render_template("operational_report.html", report=report)
        finally:
            db.close()

    @app.route("/ml-experiment")
    @require_auth
    def ml_experiment_view():
        """Educational Scikit-Learn Experiment view with explicit non-clinical labeling."""
        ml_data = run_educational_ml_experiment()
        return render_template("ml_experiment.html", ml=ml_data)

    @app.route("/api-docs")
    @require_auth
    def api_docs_view():
        """Interactive REST API documentation and tester."""
        return render_template(
            "api_docs.html",
            rule_definitions=RULE_DEFINITIONS,
            measurement_specs=MEASUREMENT_SPECS
        )

    # 404 Handler
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5050, debug=False)
