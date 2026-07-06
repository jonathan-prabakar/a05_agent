"""Assemble patient context for the care manager agent."""
import sqlite3
from pathlib import Path


DB_PATH = Path("data/a05_lpr.sqlite")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    """
    Convert sqlite3.Row into a regular dictionary.
    """
    if row is None:
        return None

    return dict(row)


def rows_to_dicts(rows):
    """
    Convert multiple sqlite3.Row records into dictionaries.
    """
    return [dict(row) for row in rows]


def get_patient_demographics(conn, patient_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            patient_id,
            first_name,
            last_name,
            first_name || ' ' || last_name AS patient_name,
            date_of_birth,
            pcp_name,
            enrollment_date,
            active
        FROM patients
        WHERE patient_id = ?
        """,
        (patient_id,)
    )

    return row_to_dict(cursor.fetchone())


def get_patient_risk_summary(conn, patient_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            patient_id,
            risk_tier,
            score_date,
            model_version
        FROM risk_scores
        WHERE patient_id = ?
        ORDER BY score_date ASC
        """,
        (patient_id,)
    )

    risk_rows = rows_to_dicts(cursor.fetchall())

    if not risk_rows:
        return {
            "history": [],
            "baseline_risk_tier": None,
            "current_risk_tier": None,
            "risk_tier_delta": None
        }

    baseline = risk_rows[0]
    current = risk_rows[-1]

    return {
        "history": risk_rows,
        "baseline_risk_tier": baseline["risk_tier"],
        "current_risk_tier": current["risk_tier"],
        "risk_tier_delta": current["risk_tier"] - baseline["risk_tier"]
    }


def get_open_care_gaps(conn, patient_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            measure_name,
            status,
            due_date,
            priority
        FROM care_gaps
        WHERE patient_id = ?
          AND status = 'open'
        ORDER BY priority DESC, due_date ASC
        """,
        (patient_id,)
    )

    return rows_to_dicts(cursor.fetchall())


def get_recent_encounters(conn, patient_id, days=90):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            encounter_type,
            encounter_date,
            discharge_flag,
            summary
        FROM encounters
        WHERE patient_id = ?
          AND date(encounter_date) >= date('now', ?)
        ORDER BY encounter_date DESC
        """,
        (patient_id, f"-{days} days")
    )

    return rows_to_dicts(cursor.fetchall())


def get_medication_issues(conn, patient_id):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            medication_name,
            adherence_flag,
            event_date
        FROM medication_events
        WHERE patient_id = ?
          AND adherence_flag IN ('late_refill', 'missed_dose', 'non_adherent')
        ORDER BY event_date DESC
        """,
        (patient_id,)
    )

    return rows_to_dicts(cursor.fetchall())


def get_recent_care_manager_notes(conn, patient_id, days=90):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            note_type,
            note_text,
            status,
            created_at,
            snooze_until
        FROM care_manager_notes
        WHERE patient_id = ?
          AND date(created_at) >= date('now', ?)
        ORDER BY created_at DESC
        """,
        (patient_id, f"-{days} days")
    )

    return rows_to_dicts(cursor.fetchall())


def assemble_patient_context(conn, patient_id):
    """
    Assemble bounded patient context for brief generation.

    This intentionally pulls:
    - demographics
    - risk trend
    - open care gaps
    - recent encounters from last 90 days
    - medication adherence issues
    - recent care manager notes from last 90 days

    It does NOT pull the entire patient history.
    """
    patient = get_patient_demographics(conn, patient_id)

    if patient is None:
        raise ValueError(f"Patient not found: {patient_id}")

    context = {
        "patient": patient,
        "risk": get_patient_risk_summary(conn, patient_id),
        "open_care_gaps": get_open_care_gaps(conn, patient_id),
        "recent_encounters": get_recent_encounters(conn, patient_id, days=90),
        "medication_issues": get_medication_issues(conn, patient_id),
        "care_manager_notes": get_recent_care_manager_notes(conn, patient_id, days=90),
    }

    return context


def print_patient_context(context):
    patient = context["patient"]
    risk = context["risk"]

    print("\n==============================")
    print("PATIENT CONTEXT")
    print("==============================")
    print(f"Patient: {patient['patient_name']} ({patient['patient_id']})")
    print(f"PCP: {patient['pcp_name']}")
    print(f"DOB: {patient['date_of_birth']}")
    print(f"Enrollment date: {patient['enrollment_date']}")

    print("\nRisk Summary")
    print("------------------------------")
    print(f"Baseline risk tier: {risk['baseline_risk_tier']}")
    print(f"Current risk tier: {risk['current_risk_tier']}")
    print(f"Risk tier delta: {risk['risk_tier_delta']}")

    print("\nOpen Care Gaps")
    print("------------------------------")
    if context["open_care_gaps"]:
        for gap in context["open_care_gaps"]:
            print(
                f"- {gap['measure_name']} "
                f"| Due: {gap['due_date']} "
                f"| Priority: {gap['priority']}"
            )
    else:
        print("No open care gaps.")

    print("\nRecent Encounters")
    print("------------------------------")
    if context["recent_encounters"]:
        for encounter in context["recent_encounters"]:
            print(
                f"- {encounter['encounter_date']} "
                f"| {encounter['encounter_type']} "
                f"| Discharge: {encounter['discharge_flag']}"
            )
            print(f"  Summary: {encounter['summary']}")
    else:
        print("No recent encounters.")

    print("\nMedication Issues")
    print("------------------------------")
    if context["medication_issues"]:
        for med in context["medication_issues"]:
            print(
                f"- {med['medication_name']} "
                f"| {med['adherence_flag']} "
                f"| {med['event_date']}"
            )
    else:
        print("No medication adherence issues.")

    print("\nCare Manager Notes")
    print("------------------------------")
    if context["care_manager_notes"]:
        for note in context["care_manager_notes"]:
            print(
                f"- {note['created_at']} "
                f"| {note['note_type']} "
                f"| Status: {note['status']}"
            )
            print(f"  Note: {note['note_text']}")
            if note["snooze_until"]:
                print(f"  Snoozed until: {note['snooze_until']}")
    else:
        print("No recent care manager notes.")


def main():
    conn = connect_db()

    patient_id = "P_DEMO_005"
    context = assemble_patient_context(conn, patient_id)

    conn.close()

    print_patient_context(context)


if __name__ == "__main__":
    main()