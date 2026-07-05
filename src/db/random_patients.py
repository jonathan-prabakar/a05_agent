import random
from datetime import datetime, timedelta

from seed_helpers import (
    insert_patient,
    insert_risk_score,
    insert_care_gap,
    insert_encounter,
    insert_medication_event,
    insert_care_manager_note,
)


FIRST_NAMES = [
    "James", "Linda", "Robert", "Patricia", "Michael", "Barbara",
    "William", "Elizabeth", "Jennifer", "Richard", "Susan", "Joseph",
    "Karen", "Thomas", "Nancy", "Daniel", "Lisa", "Matthew", "Carlos",
    "Mei", "Priya", "Samir", "Fatima", "Grace", "Omar", "Elena", "Noah"
]

LAST_NAMES = [
    "Smith", "Chen", "Kim", "Patel", "Garcia", "Brown", "Johnson",
    "Martinez", "Davis", "Wilson", "Anderson", "Thomas", "Moore",
    "Taylor", "Nguyen", "Shah", "Rodriguez", "Lee", "Walker"
]

PCP_NAMES = [
    "Dr. Shah",
    "Dr. Kim",
    "Dr. Hernandez",
    "Dr. Patel",
    "Dr. Wilson",
    "Dr. Nguyen",
    "Dr. Cooper"
]

CARE_GAP_MEASURES = [
    "A1C screening",
    "Blood pressure follow-up",
    "Medication reconciliation",
    "Annual wellness visit",
    "Diabetic eye exam",
    "Colorectal cancer screening",
    "Statin therapy review",
    "Kidney function screening"
]

MEDICATIONS = [
    "Metformin",
    "Lisinopril",
    "Atorvastatin",
    "Amlodipine",
    "Insulin glargine",
    "Losartan",
    "Carvedilol",
    "Furosemide"
]

ENCOUNTER_TYPES = [
    "Primary care visit",
    "Emergency department visit",
    "Hospital admission",
    "Specialist visit",
    "Telehealth visit"
]


def random_date_between(days_ago_start, days_ago_end):
    """
    Return a date string between two day offsets from today.

    Example:
    random_date_between(1, 30) gives a date from 1-30 days ago.
    random_date_between(-30, 90) can produce future due dates and overdue dates.
    """
    days_ago = random.randint(days_ago_start, days_ago_end)
    date = datetime.now() - timedelta(days=days_ago)
    return date.strftime("%Y-%m-%d")


def generate_dob():
    """
    Generate adult synthetic DOBs between roughly age 35 and 85.
    """
    age = random.randint(35, 85)
    birth_year = datetime.now().year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)

    return f"{birth_year}-{birth_month:02d}-{birth_day:02d}"


def generate_random_patient_id(index):
    """
    Generate random patient IDs that do not collide with demo patient IDs.
    """
    return f"P{index:04d}"


def seed_random_patients(conn, count=95):
    """
    Seed a group of random synthetic patients.

    These are background patients that make the queue realistic.
    The deterministic demo patients remain the main scripted examples.
    """
    for i in range(1, count + 1):
        patient_id = generate_random_patient_id(i)

        insert_patient(
            conn=conn,
            patient_id=patient_id,
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            date_of_birth=generate_dob(),
            pcp_name=random.choice(PCP_NAMES),
            enrollment_date=random_date_between(180, 1500),
            active=1
        )

        seed_random_risk_history(conn, patient_id)
        seed_random_care_gaps(conn, patient_id)
        seed_random_encounters(conn, patient_id)
        seed_random_medication_events(conn, patient_id)
        maybe_seed_random_care_manager_note(conn, patient_id)

    print(f"Seeded {count} random patients.")


def seed_random_risk_history(conn, patient_id):
    """
    Create 3 risk snapshots across 90 days.

    Most patients are stable or change slightly.
    """
    base_tier = random.choices(
        population=[1, 2, 3, 4, 5],
        weights=[25, 35, 25, 12, 3],
        k=1
    )[0]

    tier_90_days_ago = base_tier
    tier_45_days_ago = max(1, min(5, base_tier + random.choice([-1, 0, 0, 1])))
    current_tier = max(1, min(5, tier_45_days_ago + random.choice([-1, 0, 0, 1])))

    risk_history = [
        {"days_ago": 90, "risk_tier": tier_90_days_ago},
        {"days_ago": 45, "risk_tier": tier_45_days_ago},
        {"days_ago": 0, "risk_tier": current_tier},
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


def seed_random_care_gaps(conn, patient_id):
    """
    Generate 0-5 care gaps.

    Most patients get 0-2.
    A smaller number get 3-5.
    """
    gap_count = random.choices(
        population=[0, 1, 2, 3, 4, 5],
        weights=[25, 30, 25, 12, 6, 2],
        k=1
    )[0]

    if gap_count == 0:
        return

    selected_measures = random.sample(
        CARE_GAP_MEASURES,
        k=min(gap_count, len(CARE_GAP_MEASURES))
    )

    for measure in selected_measures:
        status = random.choices(
            population=["open", "closed"],
            weights=[80, 20],
            k=1
        )[0]

        insert_care_gap(
            conn=conn,
            patient_id=patient_id,
            measure_name=measure,
            status=status,
            due_date=random_date_between(-30, 90),
            priority=random.randint(1, 3)
        )


def seed_random_encounters(conn, patient_id):
    """
    Generate 0-4 encounters.
    Some ED visits or admissions count as discharges.
    """
    encounter_count = random.choices(
        population=[0, 1, 2, 3, 4],
        weights=[20, 35, 25, 15, 5],
        k=1
    )[0]

    for _ in range(encounter_count):
        encounter_type = random.choice(ENCOUNTER_TYPES)

        discharge_flag = 0

        if encounter_type in ["Emergency department visit", "Hospital admission"]:
            discharge_flag = 1 if random.random() < 0.35 else 0

        summary = generate_encounter_summary(encounter_type, discharge_flag)

        insert_encounter(
            conn=conn,
            patient_id=patient_id,
            encounter_type=encounter_type,
            encounter_date=random_date_between(1, 120),
            discharge_flag=discharge_flag,
            summary=summary
        )


def generate_encounter_summary(encounter_type, discharge_flag):
    """
    Generate a short synthetic encounter summary.
    """
    if discharge_flag:
        return (
            f"{encounter_type}. Patient discharged with recommendation "
            f"for follow-up and medication review."
        )

    return (
        f"{encounter_type}. Routine synthetic documentation available. "
        f"No urgent action recorded."
    )


def seed_random_medication_events(conn, patient_id):
    """
    Generate 0-3 medication events.
    Some events include adherence issues.
    """
    event_count = random.choices(
        population=[0, 1, 2, 3],
        weights=[35, 35, 20, 10],
        k=1
    )[0]

    adherence_flags = [
        "on_track",
        "on_track",
        "on_track",
        "late_refill",
        "missed_dose",
        "non_adherent"
    ]

    for _ in range(event_count):
        insert_medication_event(
            conn=conn,
            patient_id=patient_id,
            medication_name=random.choice(MEDICATIONS),
            adherence_flag=random.choice(adherence_flags),
            event_date=random_date_between(1, 60)
        )


def maybe_seed_random_care_manager_note(conn, patient_id):
    """
    Randomly add a care manager note to some patients.

    A small number are snoozed to test memory behavior.
    """
    if random.random() > 0.15:
        return

    created_at = random_date_between(1, 30)

    if random.random() < 0.30:
        snooze_until = (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
        status = "snoozed"
        note_text = "Synthetic care manager note: patient temporarily snoozed."
    else:
        snooze_until = None
        status = "pending_review"
        note_text = "Synthetic AI-drafted care manager note pending review."

    insert_care_manager_note(
        conn=conn,
        patient_id=patient_id,
        note_type="care_manager_update",
        note_text=note_text,
        status=status,
        created_at=created_at,
        snooze_until=snooze_until
    )