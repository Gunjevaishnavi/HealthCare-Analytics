"""
REST APIs for Synthetic Patient, Visit, Measurement, and Risk Indicator Records
-------------------------------------------------------------------------------
Strictly educational analytics. All records are synthetic.
"""

from flask import Blueprint, request, jsonify
import datetime
import uuid

from backend.database import SessionLocal, Patient, Visit, Measurement, RiskIndicator, Department
from backend.auth import require_api_key
from backend.rules_engine import (
    validate_measurement_value, evaluate_patient_indicators,
    MEASUREMENT_SPECS, RULE_DEFINITIONS
)
from backend.config import Config

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# ---------------- PATIENTS API ---------------- #

@api_bp.route("/patients", methods=["GET"])
@require_api_key
def get_patients():
    """Returns paginated synthetic patient records with optional filtering."""
    db = SessionLocal()
    try:
        age_band = request.args.get("age_band")
        gender = request.args.get("gender")
        chronic = request.args.get("chronic")
        search = request.args.get("search")
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))

        query = db.query(Patient)
        if age_band:
            query = query.filter(Patient.age_band == age_band)
        if gender:
            query = query.filter(Patient.gender == gender)
        if chronic is not None:
            c_val = chronic.lower() in ("true", "1", "yes")
            query = query.filter(Patient.chronic_condition_flag == c_val)
        if search:
            query = query.filter(Patient.patient_id.like(f"%{search}%"))

        total_count = query.count()
        patients = query.order_by(Patient.patient_id).offset(offset).limit(limit).all()

        return jsonify({
            "status": "success",
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT,
            "data": [p.to_dict() for p in patients]
        }), 200
    finally:
        db.close()


@api_bp.route("/patients", methods=["POST"])
@require_api_key
def create_patient():
    """Creates a new synthetic/de-identified patient record."""
    data = request.get_json(silent=True) or {}
    age_band = data.get("age_band")
    if not age_band:
        return jsonify({"error": "Missing required field: 'age_band'"}), 400

    db = SessionLocal()
    try:
        pat_id = data.get("patient_id") or f"PAT-SYN-{uuid.uuid4().hex[:6].upper()}"
        
        # Check if already exists
        if db.query(Patient).filter(Patient.patient_id == pat_id).first():
            return jsonify({"error": f"Patient ID '{pat_id}' already exists."}), 409

        patient = Patient(
            patient_id=pat_id,
            age_band=age_band,
            gender=data.get("gender", "Undisclosed"),
            ethnicity_code=data.get("ethnicity_code", "ETH_A1"),
            residence_region=data.get("residence_region", "Urban-Central"),
            chronic_condition_flag=bool(data.get("chronic_condition_flag", False)),
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

        return jsonify({
            "status": "created",
            "message": "Synthetic patient record registered successfully.",
            "data": patient.to_dict()
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@api_bp.route("/patients/<patient_id>", methods=["GET"])
@require_api_key
def get_patient_detail(patient_id):
    """Retrieves detailed profile, visits, latest measurements, and active risk indicators."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return jsonify({"error": f"Patient '{patient_id}' not found."}), 404

        visits = [v.to_dict() for v in patient.visits]
        measurements = [m.to_dict() for m in patient.measurements]
        indicators = [i.to_dict() for i in patient.risk_indicators]

        return jsonify({
            "patient": patient.to_dict(),
            "visits": visits,
            "measurements": measurements,
            "risk_indicators": indicators,
            "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT
        }), 200
    finally:
        db.close()


# ---------------- VISITS API ---------------- #

@api_bp.route("/visits", methods=["GET"])
@require_api_key
def get_visits():
    """Lists synthetic visits with department & admission type filters."""
    db = SessionLocal()
    try:
        dept_id = request.args.get("department_id")
        adm_type = request.args.get("admission_type")
        pat_id = request.args.get("patient_id")
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))

        query = db.query(Visit)
        if dept_id:
            query = query.filter(Visit.department_id == dept_id)
        if adm_type:
            query = query.filter(Visit.admission_type == adm_type)
        if pat_id:
            query = query.filter(Visit.patient_id == pat_id)

        total_count = query.count()
        visits = query.order_by(Visit.visit_date.desc()).offset(offset).limit(limit).all()

        return jsonify({
            "status": "success",
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "data": [v.to_dict() for v in visits]
        }), 200
    finally:
        db.close()


@api_bp.route("/visits", methods=["POST"])
@require_api_key
def create_visit():
    """Records a new clinical encounter/visit."""
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id")
    dept_id = data.get("department_id")

    if not patient_id or not dept_id:
        return jsonify({"error": "patient_id and department_id are required fields."}), 400

    db = SessionLocal()
    try:
        # Check patient and department exist
        if not db.query(Patient).filter(Patient.patient_id == patient_id).first():
            return jsonify({"error": f"Patient '{patient_id}' not found."}), 404
        if not db.query(Department).filter(Department.department_id == dept_id).first():
            return jsonify({"error": f"Department '{dept_id}' not found."}), 404

        visit_id = data.get("visit_id") or f"VIS-{patient_id}-{uuid.uuid4().hex[:4].upper()}"
        visit_date = datetime.datetime.now(datetime.timezone.utc)
        admission_type = data.get("admission_type", "Routine Outpatient")

        visit = Visit(
            visit_id=visit_id,
            patient_id=patient_id,
            department_id=dept_id,
            visit_date=visit_date,
            admission_type=admission_type,
            status="Completed"
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)

        return jsonify({
            "status": "created",
            "message": "Visit record recorded successfully.",
            "data": visit.to_dict()
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ---------------- MEASUREMENTS API & VALIDATION ---------------- #

@api_bp.route("/measurements", methods=["GET"])
@require_api_key
def get_measurements():
    """Queries health measurements with validation status filtering."""
    db = SessionLocal()
    try:
        patient_id = request.args.get("patient_id")
        measure_type = request.args.get("measure_type")
        status = request.args.get("validation_status")
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = int(request.args.get("offset", 0))

        query = db.query(Measurement)
        if patient_id:
            query = query.filter(Measurement.patient_id == patient_id)
        if measure_type:
            query = query.filter(Measurement.measure_type == measure_type)
        if status:
            query = query.filter(Measurement.validation_status == status)

        total_count = query.count()
        measurements = query.order_by(Measurement.measurement_date.desc()).offset(offset).limit(limit).all()

        return jsonify({
            "status": "success",
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "data": [m.to_dict() for m in measurements]
        }), 200
    finally:
        db.close()


@api_bp.route("/measurements", methods=["POST"])
@require_api_key
def create_measurement():
    """
    Submits a new health measurement.
    Automatically validates the measurement value against documented physiological assumptions.
    """
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id")
    measure_type = data.get("measure_type")
    value = data.get("value")

    if not patient_id or not measure_type or value is None:
        return jsonify({"error": "patient_id, measure_type, and numeric value are required."}), 400

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return jsonify({"error": "value must be a valid number."}), 400

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return jsonify({"error": f"Patient '{patient_id}' not found."}), 404

        # Run validation engine against documented sample assumptions
        is_valid, val_status, message = validate_measurement_value(measure_type, val_float)
        spec = MEASUREMENT_SPECS.get(measure_type, {})
        unit = data.get("unit") or spec.get("unit", "units")

        meas_id = f"M-{uuid.uuid4().hex[:12]}"
        meas = Measurement(
            measurement_id=meas_id,
            patient_id=patient_id,
            visit_id=data.get("visit_id"),
            measurement_date=datetime.datetime.now(datetime.timezone.utc),
            measure_type=measure_type,
            value=round(val_float, 2),
            unit=unit,
            is_valid_range=is_valid,
            validation_status=val_status
        )
        db.add(meas)
        db.commit()
        db.refresh(meas)

        # Trigger automatic re-evaluation of transparent risk indicators for this patient
        latest_meas = {}
        for m in patient.measurements:
            if m.is_valid_range:
                latest_meas[m.measure_type] = m.value
        
        triggered = evaluate_patient_indicators(latest_meas)
        # Clear old indicators and persist updated ones
        db.query(RiskIndicator).filter(RiskIndicator.patient_id == patient_id).delete()
        for rule in triggered:
            ind = RiskIndicator(
                indicator_id=f"IND-{patient_id}-{rule['rule_code']}",
                patient_id=patient_id,
                rule_code=rule["rule_code"],
                indicator_value=rule["indicator_value"],
                indicator_category=rule["indicator_category"],
                rationale=rule["rationale"],
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(ind)
        db.commit()

        return jsonify({
            "status": "created",
            "measurement": meas.to_dict(),
            "validation": {
                "is_valid_range": is_valid,
                "status": val_status,
                "explanation": message,
                "documented_reference_range": f"{spec.get('normal_min')} - {spec.get('normal_max')} {unit}" if spec else "N/A"
            },
            "active_indicators_after_update": len(triggered)
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@api_bp.route("/measurements/validate", methods=["POST"])
def validate_measurement_adhoc():
    """Validates an ad-hoc measurement value without saving to database."""
    data = request.get_json(silent=True) or {}
    measure_type = data.get("measure_type")
    value = data.get("value")

    if not measure_type or value is None:
        return jsonify({"error": "measure_type and value are required."}), 400

    try:
        val_float = float(value)
    except (ValueError, TypeError):
        return jsonify({"error": "value must be numeric."}), 400

    is_valid, status, msg = validate_measurement_value(measure_type, val_float)
    spec = MEASUREMENT_SPECS.get(measure_type, {})

    return jsonify({
        "measure_type": measure_type,
        "input_value": val_float,
        "unit": spec.get("unit", ""),
        "is_valid_range": is_valid,
        "validation_status": status,
        "message": msg,
        "documented_assumptions": spec
    }), 200


# ---------------- RISK INDICATORS API ---------------- #

@api_bp.route("/indicators", methods=["GET"])
@require_api_key
def get_indicators():
    """Lists computed risk indicators with rule documentation and limitations."""
    db = SessionLocal()
    try:
        rule_code = request.args.get("rule_code")
        patient_id = request.args.get("patient_id")
        limit = min(int(request.args.get("limit", 100)), 300)

        query = db.query(RiskIndicator)
        if rule_code:
            query = query.filter(RiskIndicator.rule_code == rule_code)
        if patient_id:
            query = query.filter(RiskIndicator.patient_id == patient_id)

        indicators = query.order_by(RiskIndicator.created_at.desc()).limit(limit).all()

        return jsonify({
            "status": "success",
            "count": len(indicators),
            "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT,
            "data": [i.to_dict() for i in indicators]
        }), 200
    finally:
        db.close()


@api_bp.route("/indicators/rules", methods=["GET"])
def get_rule_specifications():
    """Returns transparent specifications of all illustrative indicator rules."""
    return jsonify({
        "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT,
        "clinical_validity_claim": False,
        "purpose": "Educational population risk indicator demonstration.",
        "rules": RULE_DEFINITIONS,
        "measurement_reference_ranges": MEASUREMENT_SPECS
    }), 200


@api_bp.route("/indicators/evaluate/<patient_id>", methods=["POST"])
@require_api_key
def evaluate_patient(patient_id):
    """Triggers on-demand evaluation of transparent rules for a patient."""
    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return jsonify({"error": f"Patient '{patient_id}' not found."}), 404

        latest_meas = {}
        for m in patient.measurements:
            if m.is_valid_range:
                latest_meas[m.measure_type] = m.value

        triggered = evaluate_patient_indicators(latest_meas)

        # Clear and update in DB
        db.query(RiskIndicator).filter(RiskIndicator.patient_id == patient_id).delete()
        new_indicators = []
        for rule in triggered:
            ind = RiskIndicator(
                indicator_id=f"IND-{patient_id}-{rule['rule_code']}",
                patient_id=patient_id,
                rule_code=rule["rule_code"],
                indicator_value=rule["indicator_value"],
                indicator_category=rule["indicator_category"],
                rationale=rule["rationale"],
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(ind)
            new_indicators.append(ind)
        db.commit()

        return jsonify({
            "patient_id": patient_id,
            "active_indicators_count": len(triggered),
            "evaluated_measurements": latest_meas,
            "triggered_rules": triggered,
            "disclaimer": Config.MANDATORY_LIMITATIONS_STATEMENT
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
