def clear_existing_data(conn):
    """
    Clear all existing data from the database.

    Child tables are cleared before parent tables to avoid
    foreign key relationship problems.
    """
    cursor = conn.cursor()

    tables = [
        "care_manager_notes",
        "medication_events",
        "encounters",
        "care_gaps",
        "risk_scores",
        "patients"
    ]

    for table in tables:
        cursor.execute(f"DELETE FROM {table}")

    print("Cleared existing data.")


def insert_patient(
    conn,
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    pcp_name,
    enrollment_date,
    active=1
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO patients (
            patient_id,
            first_name,
            last_name,
            date_of_birth,
            pcp_name,
            enrollment_date,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            first_name,
            last_name,
            date_of_birth,
            pcp_name,
            enrollment_date,
            active
        )
    )


def insert_risk_score(
    conn,
    patient_id,
    risk_tier,
    score_date,
    model_version="A01-v1"
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO risk_scores (
            patient_id,
            risk_tier,
            score_date,
            model_version
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            patient_id,
            risk_tier,
            score_date,
            model_version
        )
    )


def insert_care_gap(
    conn,
    patient_id,
    measure_name,
    status,
    due_date,
    priority
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO care_gaps (
            patient_id,
            measure_name,
            status,
            due_date,
            priority
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            measure_name,
            status,
            due_date,
            priority
        )
    )


def insert_encounter(
    conn,
    patient_id,
    encounter_type,
    encounter_date,
    discharge_flag,
    summary
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO encounters (
            patient_id,
            encounter_type,
            encounter_date,
            discharge_flag,
            summary
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            encounter_type,
            encounter_date,
            discharge_flag,
            summary
        )
    )


def insert_medication_event(
    conn,
    patient_id,
    medication_name,
    adherence_flag,
    event_date
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO medication_events (
            patient_id,
            medication_name,
            adherence_flag,
            event_date
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            patient_id,
            medication_name,
            adherence_flag,
            event_date
        )
    )


def insert_care_manager_note(
    conn,
    patient_id,
    note_type,
    note_text,
    status,
    created_at,
    snooze_until=None
):
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO care_manager_notes (
            patient_id,
            note_type,
            note_text,
            status,
            created_at,
            snooze_until
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            patient_id,
            note_type,
            note_text,
            status,
            created_at,
            snooze_until
        )
    )