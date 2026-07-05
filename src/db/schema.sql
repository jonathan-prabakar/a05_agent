CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT,
    pcp_name TEXT,
    enrollment_date TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS risk_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    risk_tier INTEGER NOT NULL,
    score_date TEXT NOT NULL,
    model_version TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS care_gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    measure_name TEXT NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT,
    priority INTEGER,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS encounters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    encounter_type TEXT,
    encounter_date TEXT,
    discharge_flag INTEGER DEFAULT 0,
    summary TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS medication_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    medication_name TEXT,
    adherence_flag TEXT,
    event_date TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE IF NOT EXISTS care_manager_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    note_type TEXT,
    note_text TEXT,
    status TEXT,
    created_at TEXT,
    snooze_until TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);