PRAGMA foreign_keys = ON;

CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY CHECK (patient_id GLOB 'PAT-SYN-[0-9][0-9][0-9]'),
    synthetic INTEGER NOT NULL CHECK (synthetic = 1),
    age_years INTEGER NOT NULL CHECK (age_years BETWEEN 18 AND 120),
    last_review_date TEXT NOT NULL
);

CREATE TABLE conditions (
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    condition_code TEXT NOT NULL CHECK (condition_code IN ('HAS', 'DM2')),
    PRIMARY KEY (patient_id, condition_code)
);

CREATE TABLE allergies (
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    substance TEXT NOT NULL,
    PRIMARY KEY (patient_id, substance)
);

CREATE TABLE medications (
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    medication_label TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    PRIMARY KEY (patient_id, medication_label)
);

CREATE TABLE exams (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    exam_code TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'pending')),
    requested_at TEXT NOT NULL,
    completed_at TEXT,
    result_summary TEXT,
    CHECK (
        (status = 'pending' AND completed_at IS NULL AND result_summary IS NULL)
        OR
        (status = 'completed' AND completed_at IS NOT NULL AND result_summary IS NOT NULL)
    ),
    UNIQUE (patient_id, exam_code, requested_at)
);

CREATE TABLE visits (
    visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    occurred_at TEXT NOT NULL,
    visit_type TEXT NOT NULL,
    synthetic_summary TEXT NOT NULL
);

CREATE INDEX idx_exams_patient_status ON exams(patient_id, status);
CREATE INDEX idx_visits_patient_date ON visits(patient_id, occurred_at DESC);

