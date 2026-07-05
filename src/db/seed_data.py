import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

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

    conn.commit()

    print("Cleared existing data.")


def insert_test_patient(conn):
    """
    Insert one test patient into the patients table.
    """
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
            "P_TEST_001",
            "Maria",
            "Lopez",
            "1958-04-12",
            "Dr. Shah",
            "2022-01-15",
            1
        )
    )

    conn.commit()

    print("Inserted test patient: P_TEST_001")

def insert_risk_score(conn, patient_id, risk_tier, score_date, model_version="A01-v1"):
    """
    Insert one risk score record for a patient.
    """
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


def insert_test_patient_risk_history(conn):
    """
    Insert 3 risk score snapshots for the test patient.
    This creates a risk tier jump from 2 to 4.
    """
    patient_id = "P_TEST_001"

    risk_history = [
        {
            "days_ago": 90,
            "risk_tier": 2
        },
        {
            "days_ago": 45,
            "risk_tier": 3
        },
        {
            "days_ago": 0,
            "risk_tier": 4
        }
    ]

    for record in risk_history:
        score_date = datetime.now() - timedelta(days=record["days_ago"])
        score_date_string = score_date.strftime("%Y-%m-%d")

        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=record["risk_tier"],
            score_date=score_date_string
        )

    conn.commit()

    print("Inserted risk history for patient: P_TEST_001")

def insert_care_gap(conn, patient_id, measure_name, status, due_date, priority):
    """
    Insert one care gap for a patient.
    """
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


def insert_test_patient_care_gaps(conn):
    """
    Insert multiple care gaps for the test patient.
    """
    patient_id = "P_TEST_001"

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
        due_date_string = due_date.strftime("%Y-%m-%d")

        insert_care_gap(
            conn=conn,
            patient_id=patient_id,
            measure_name=gap["measure_name"],
            status=gap["status"],
            due_date=due_date_string,
            priority=gap["priority"]
        )

    conn.commit()

    print("Inserted care gaps for patient: P_TEST_001")

def insert_encounter(
    conn,
    patient_id,
    encounter_type,
    encounter_date,
    discharge_flag,
    summary
):
    """
    Insert one encounter record for a patient.
    """
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


def insert_test_patient_encounters(conn):
    """
    Insert recent encounter data for the test patient.
    Includes one recent discharge.
    """
    patient_id = "P_TEST_001"

    encounter_date = datetime.now() - timedelta(days=3)
    encounter_date_string = encounter_date.strftime("%Y-%m-%d")

    insert_encounter(
        conn=conn,
        patient_id=patient_id,
        encounter_type="Hospital admission",
        encounter_date=encounter_date_string,
        discharge_flag=1,
        summary=(
            "Synthetic discharge summary: patient discharged after inpatient stay. "
            "Follow-up appointment and medication reconciliation recommended."
        )
    )

    conn.commit()

    print("Inserted encounters for patient: P_TEST_001")

def main():
    conn = connect_db()

    print("Connected to database successfully.")
    print(f"Database path: {DB_PATH}")

    show_existing_tables(conn)
    clear_existing_data(conn)
    insert_test_patient(conn)
    insert_test_patient_risk_history(conn)
    insert_test_patient_care_gaps(conn)
    insert_test_patient_encounters(conn)

    conn.close()


if __name__ == "__main__":
    main()