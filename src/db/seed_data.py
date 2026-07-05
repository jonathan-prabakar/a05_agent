import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

from seed_helpers import (
    clear_existing_data,
    insert_patient,
    insert_risk_score,
    insert_care_gap,
    insert_encounter,
    insert_medication_event,
    insert_care_manager_note,
)


DB_PATH = Path("data/a05_lpr.sqlite")


def connect_db():
    """
    Connect to the SQLite database.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return conn


def show_existing_tables(conn):
    """
    Print all tables currently inside the SQLite database.
    """
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
        """
    )

    tables = cursor.fetchall()

    print("Existing tables:")

    if not tables:
        print("No tables found.")
        return

    for table in tables:
        print(f"- {table[0]}")


def seed_test_patient(conn):
    """
    Seed one complete test patient.

    This patient intentionally has multiple signals:
    - risk tier jump
    - open care gaps
    - recent discharge
    - medication adherence issues
    - AI-drafted note pending review
    """
    patient_id = "P_TEST_001"

    insert_patient(
        conn=conn,
        patient_id=patient_id,
        first_name="Maria",
        last_name="Lopez",
        date_of_birth="1958-04-12",
        pcp_name="Dr. Shah",
        enrollment_date="2022-01-15",
        active=1
    )

    risk_history = [
        {"days_ago": 90, "risk_tier": 2},
        {"days_ago": 45, "risk_tier": 3},
        {"days_ago": 0, "risk_tier": 4},
    ]

    for record in risk_history:
        score_date = datetime.now() - timedelta(days=record["days_ago"])

        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=record["risk_tier"],
            score_date=score_date.strftime("%Y-%m-%d"),
            model_version="A01-v1"
        )

    care_gaps = [
        {
            "measure_name": "Medication reconciliation",
            "status": "open",
            "days_until_due": 7,
            "priority": 3
        },
        {
            "measure_name": "A1C screening",
            "status": "open",
            "days_until_due": 14,
            "priority": 2
        },
        {
            "measure_name": "Annual wellness visit",
            "status": "closed",
            "days_until_due": -10,
            "priority": 1
        }
    ]

    for gap in care_gaps:
        due_date = datetime.now() + timedelta(days=gap["days_until_due"])

        insert_care_gap(
            conn=conn,
            patient_id=patient_id,
            measure_name=gap["measure_name"],
            status=gap["status"],
            due_date=due_date.strftime("%Y-%m-%d"),
            priority=gap["priority"]
        )

    encounter_date = datetime.now() - timedelta(days=3)

    insert_encounter(
        conn=conn,
        patient_id=patient_id,
        encounter_type="Hospital admission",
        encounter_date=encounter_date.strftime("%Y-%m-%d"),
        discharge_flag=1,
        summary=(
            "Synthetic discharge summary: patient discharged after inpatient stay. "
            "Follow-up appointment and medication reconciliation recommended."
        )
    )

    medication_events = [
        {
            "medication_name": "Metformin",
            "adherence_flag": "late_refill",
            "days_ago": 12
        },
        {
            "medication_name": "Lisinopril",
            "adherence_flag": "non_adherent",
            "days_ago": 8
        },
        {
            "medication_name": "Atorvastatin",
            "adherence_flag": "on_track",
            "days_ago": 20
        }
    ]

    for event in medication_events:
        event_date = datetime.now() - timedelta(days=event["days_ago"])

        insert_medication_event(
            conn=conn,
            patient_id=patient_id,
            medication_name=event["medication_name"],
            adherence_flag=event["adherence_flag"],
            event_date=event_date.strftime("%Y-%m-%d")
        )

    insert_care_manager_note(
        conn=conn,
        patient_id=patient_id,
        note_type="ai_drafted_brief",
        note_text=(
            "AI-drafted care manager brief. Patient has rising risk tier, "
            "recent discharge, open care gaps, and medication adherence issues. "
            "This note is unsigned and pending human review."
        ),
        status="pending_review",
        created_at=datetime.now().strftime("%Y-%m-%d"),
        snooze_until=None
    )

    print("Seeded test patient: P_TEST_001")


def main():
    conn = connect_db()

    print("Connected to database successfully.")
    print(f"Database path: {DB_PATH}")

    show_existing_tables(conn)
    clear_existing_data(conn)
    seed_test_patient(conn)

    conn.commit()
    conn.close()

    print("Seed data completed successfully.")


if __name__ == "__main__":
    main()