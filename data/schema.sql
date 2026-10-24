-- Healthcare Analytics and Patient Risk Indicator System
-- Database Schema for MySQL / SQLite compatible deployment
-- Educational use only with synthetic or de-identified patient data.

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    department_id VARCHAR(32) PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    wing VARCHAR(50) NULL,
    capacity INT DEFAULT 50
);

-- 2. Patients Table (Suggested Entity)
-- Fields: patient_id, age_band, optional demographic fields
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(64) PRIMARY KEY,
    age_band VARCHAR(20) NOT NULL,
    gender VARCHAR(20) NULL,
    ethnicity_code VARCHAR(20) NULL,
    residence_region VARCHAR(50) NULL,
    chronic_condition_flag BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_patients_age_band (age_band)
);

-- 3. Visits Table (Suggested Entity)
-- Fields: visit_id, patient_id, department_id, visit_date
CREATE TABLE IF NOT EXISTS visits (
    visit_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    department_id VARCHAR(32) NOT NULL,
    visit_date DATETIME NOT NULL,
    discharge_date DATETIME NULL,
    admission_type VARCHAR(50) DEFAULT 'Outpatient',
    status VARCHAR(30) DEFAULT 'Completed',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
    INDEX idx_visits_patient (patient_id),
    INDEX idx_visits_dept (department_id),
    INDEX idx_visits_date (visit_date)
);

-- 4. Measurements Table (Suggested Entity)
-- Fields: measurement_id, patient_id, measurement_date, measure_type, value, unit
CREATE TABLE IF NOT EXISTS measurements (
    measurement_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    visit_id VARCHAR(64) NULL,
    measurement_date DATETIME NOT NULL,
    measure_type VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(30) NOT NULL,
    is_valid_range BOOLEAN DEFAULT TRUE,
    validation_status VARCHAR(50) DEFAULT 'VALID',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES visits(visit_id) ON DELETE SET NULL,
    INDEX idx_meas_patient (patient_id),
    INDEX idx_meas_type (measure_type),
    INDEX idx_meas_date (measurement_date)
);

-- 5. Risk Indicators Table (Suggested Entity)
-- Fields: indicator_id, patient_id, rule_code, indicator_value, created_at
CREATE TABLE IF NOT EXISTS risk_indicators (
    indicator_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    rule_code VARCHAR(50) NOT NULL,
    indicator_value FLOAT NOT NULL,
    indicator_category VARCHAR(50) NOT NULL,
    rationale TEXT NULL,
    non_clinical_disclaimer TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    INDEX idx_ind_patient (patient_id),
    INDEX idx_ind_rule (rule_code),
    INDEX idx_ind_created (created_at)
);
