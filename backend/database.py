import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.config import Config

def get_utc_now():
    return datetime.datetime.now(datetime.timezone.utc)

Base = declarative_base()
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Context-friendly database session generator."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Department(Base):
    __tablename__ = "departments"

    department_id = Column(String(32), primary_key=True)
    department_name = Column(String(100), nullable=False)
    wing = Column(String(50), nullable=True)
    capacity = Column(Integer, default=50)

    visits = relationship("Visit", back_populates="department", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "department_id": self.department_id,
            "department_name": self.department_name,
            "wing": self.wing,
            "capacity": self.capacity
        }


class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(64), primary_key=True)
    age_band = Column(String(20), nullable=False, index=True) # e.g. 0-17, 18-35, 36-50, 51-65, 66-80, 80+
    gender = Column(String(20), nullable=True) # e.g. Male, Female, Other, Unknown
    ethnicity_code = Column(String(20), nullable=True) # De-identified category e.g. ETH_01, ETH_02
    residence_region = Column(String(50), nullable=True) # De-identified regional zone e.g. North-Zone, Urban-Central
    chronic_condition_flag = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")
    measurements = relationship("Measurement", back_populates="patient", cascade="all, delete-orphan")
    risk_indicators = relationship("RiskIndicator", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "age_band": self.age_band,
            "gender": self.gender,
            "ethnicity_code": self.ethnicity_code,
            "residence_region": self.residence_region,
            "chronic_condition_flag": bool(self.chronic_condition_flag),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "visits_count": len(self.visits) if self.visits else 0,
            "measurements_count": len(self.measurements) if self.measurements else 0,
            "active_risk_indicators": len(self.risk_indicators) if self.risk_indicators else 0
        }


class Visit(Base):
    __tablename__ = "visits"

    visit_id = Column(String(64), primary_key=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    department_id = Column(String(32), ForeignKey("departments.department_id"), nullable=False, index=True)
    visit_date = Column(DateTime, nullable=False, index=True)
    discharge_date = Column(DateTime, nullable=True)
    admission_type = Column(String(50), default="Outpatient") # Emergency, Urgent, Elective, Outpatient
    status = Column(String(30), default="Completed") # Admitted, Discharged, Completed

    patient = relationship("Patient", back_populates="visits")
    department = relationship("Department", back_populates="visits")
    measurements = relationship("Measurement", back_populates="visit", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "visit_id": self.visit_id,
            "patient_id": self.patient_id,
            "department_id": self.department_id,
            "department_name": self.department.department_name if self.department else "Unknown",
            "visit_date": self.visit_date.strftime("%Y-%m-%d %H:%M:%S") if self.visit_date else None,
            "discharge_date": self.discharge_date.strftime("%Y-%m-%d %H:%M:%S") if self.discharge_date else None,
            "admission_type": self.admission_type,
            "status": self.status
        }


class Measurement(Base):
    __tablename__ = "measurements"

    measurement_id = Column(String(64), primary_key=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    visit_id = Column(String(64), ForeignKey("visits.visit_id"), nullable=True, index=True)
    measurement_date = Column(DateTime, nullable=False, index=True)
    measure_type = Column(String(50), nullable=False, index=True) # systolic_bp, diastolic_bp, heart_rate, spo2, glucose, etc.
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    is_valid_range = Column(Boolean, default=True) # Physiological plausibility flag
    validation_status = Column(String(50), default="VALID") # VALID, OUT_OF_RANGE_HIGH, OUT_OF_RANGE_LOW, IMPLAUSIBLE

    patient = relationship("Patient", back_populates="measurements")
    visit = relationship("Visit", back_populates="measurements")

    def to_dict(self):
        return {
            "measurement_id": self.measurement_id,
            "patient_id": self.patient_id,
            "visit_id": self.visit_id,
            "measurement_date": self.measurement_date.strftime("%Y-%m-%d %H:%M:%S") if self.measurement_date else None,
            "measure_type": self.measure_type,
            "value": round(self.value, 2),
            "unit": self.unit,
            "is_valid_range": bool(self.is_valid_range),
            "validation_status": self.validation_status
        }


class RiskIndicator(Base):
    __tablename__ = "risk_indicators"

    indicator_id = Column(String(64), primary_key=True)
    patient_id = Column(String(64), ForeignKey("patients.patient_id"), nullable=False, index=True)
    rule_code = Column(String(50), nullable=False, index=True)
    indicator_value = Column(Float, nullable=False) # e.g. Score or 1.0 / 0.0 binary trigger
    indicator_category = Column(String(50), nullable=False) # Cardiovascular, Glycemic, Respiratory, Renal, Composite
    rationale = Column(Text, nullable=True) # Transparent reasoning behind trigger
    non_clinical_disclaimer = Column(Text, default=Config.MANDATORY_LIMITATIONS_STATEMENT)
    created_at = Column(DateTime, default=get_utc_now, index=True)

    patient = relationship("Patient", back_populates="risk_indicators")

    def to_dict(self):
        return {
            "indicator_id": self.indicator_id,
            "patient_id": self.patient_id,
            "rule_code": self.rule_code,
            "indicator_value": round(self.indicator_value, 2),
            "indicator_category": self.indicator_category,
            "rationale": self.rationale,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "non_clinical_disclaimer": self.non_clinical_disclaimer
        }


def init_db():
    """Create all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
