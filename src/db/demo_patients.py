from datetime import datetime, timedelta

from seed_helpers import (
    insert_patient,
    insert_risk_score,
    insert_care_gap,
    insert_encounter,
    insert_medication_event,
    insert_care_manager_note,
)


def seed_demo_patients(conn):
    """
    Seed all guaranteed demo patients.
    """
    seed_risk_jump_patient(conn)
    seed_recent_discharge_patient(conn)
    seed_many_care_gaps_patient(conn)
    seed_med_nonadherence_patient(conn)
    seed_snoozed_patient(conn)

    print("Seeded 5 demo patients.")


def seed_risk_jump_patient(conn):
    """
    Demo patient 1:
    Surfaces because risk tier increased from 2 to 4.
    """
    patient_id = "P_DEMO_001"

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

    insert_care_gap(
        conn=conn,
        patient_id=patient_id,
        measure_name="Medication reconciliation",
        status="open",
        due_date=(datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
        priority=2
    )


def seed_recent_discharge_patient(conn):
    """
    Demo patient 2:
    Surfaces because of a hospital discharge 3 days ago.
    """
    patient_id = "P_DEMO_002"

    insert_patient(
        conn=conn,
        patient_id=patient_id,
        first_name="David",
        last_name="Kim",
        date_of_birth="1949-09-03",
        pcp_name="Dr. Nguyen",
        enrollment_date="2021-08-22",
        active=1
    )

    for days_ago, tier in [(90, 3), (45, 3), (0, 3)]:
        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=tier,
            score_date=(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            model_version="A01-v1"
        )

    insert_encounter(
        conn=conn,
        patient_id=patient_id,
        encounter_type="Hospital admission",
        encounter_date=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        discharge_flag=1,
        summary=(
            "Synthetic discharge summary: patient discharged after inpatient stay. "
            "Follow-up appointment and medication reconciliation recommended."
        )
    )

    insert_care_gap(
        conn=conn,
        patient_id=patient_id,
        measure_name="Medication reconciliation",
        status="open",
        due_date=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        priority=3
    )


def seed_many_care_gaps_patient(conn):
    """
    Demo patient 3:
    Surfaces because of many open care gaps.
    """
    patient_id = "P_DEMO_003"

    insert_patient(
        conn=conn,
        patient_id=patient_id,
        first_name="Ana",
        last_name="Patel",
        date_of_birth="1965-11-18",
        pcp_name="Dr. Patel",
        enrollment_date="2020-03-10",
        active=1
    )

    for days_ago, tier in [(90, 2), (45, 2), (0, 3)]:
        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=tier,
            score_date=(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            model_version="A01-v1"
        )

    care_gaps = [
        "A1C screening",
        "Blood pressure follow-up",
        "Annual wellness visit",
        "Diabetic eye exam",
        "Kidney function screening",
    ]

    for index, measure in enumerate(care_gaps):
        insert_care_gap(
            conn=conn,
            patient_id=patient_id,
            measure_name=measure,
            status="open",
            due_date=(datetime.now() + timedelta(days=7 + index * 5)).strftime("%Y-%m-%d"),
            priority=3
        )


def seed_med_nonadherence_patient(conn):
    """
    Demo patient 4:
    Surfaces because of medication adherence issues.
    """
    patient_id = "P_DEMO_004"

    insert_patient(
        conn=conn,
        patient_id=patient_id,
        first_name="James",
        last_name="Wilson",
        date_of_birth="1972-02-27",
        pcp_name="Dr. Hernandez",
        enrollment_date="2023-05-14",
        active=1
    )

    for days_ago, tier in [(90, 2), (45, 3), (0, 3)]:
        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=tier,
            score_date=(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            model_version="A01-v1"
        )

    insert_medication_event(
        conn=conn,
        patient_id=patient_id,
        medication_name="Metformin",
        adherence_flag="late_refill",
        event_date=(datetime.now() - timedelta(days=12)).strftime("%Y-%m-%d")
    )

    insert_medication_event(
        conn=conn,
        patient_id=patient_id,
        medication_name="Lisinopril",
        adherence_flag="non_adherent",
        event_date=(datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    )

    insert_care_gap(
        conn=conn,
        patient_id=patient_id,
        measure_name="A1C screening",
        status="open",
        due_date=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        priority=2
    )


def seed_snoozed_patient(conn):
    """
    Demo patient 5:
    Looks high priority, but is snoozed.
    This tests agent memory.
    """
    patient_id = "P_DEMO_005"

    insert_patient(
        conn=conn,
        patient_id=patient_id,
        first_name="Linda",
        last_name="Chen",
        date_of_birth="1955-07-08",
        pcp_name="Dr. Kim",
        enrollment_date="2019-11-02",
        active=1
    )

    for days_ago, tier in [(90, 3), (45, 4), (0, 4)]:
        insert_risk_score(
            conn=conn,
            patient_id=patient_id,
            risk_tier=tier,
            score_date=(datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            model_version="A01-v1"
        )

    insert_encounter(
        conn=conn,
        patient_id=patient_id,
        encounter_type="Emergency department visit",
        encounter_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        discharge_flag=1,
        summary="Synthetic ED discharge. Patient was recently reviewed by care manager."
    )

    insert_care_manager_note(
        conn=conn,
        patient_id=patient_id,
        note_type="queue_snooze",
        note_text="Patient reviewed yesterday. Snoozed for follow-up later this week.",
        status="snoozed",
        created_at=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        snooze_until=(datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    )