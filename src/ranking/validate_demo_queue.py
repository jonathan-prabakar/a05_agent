from rank_queue import connect_db, get_ranked_queue_data


EXPECTED_QUEUE_TYPES = {
    "P_DEMO_001": "urgent",   # Maria Lopez: risk jump 2 -> 4
    "P_DEMO_002": "urgent",   # David Kim: recent discharge
    "P_DEMO_003": "routine",  # Ana Patel: many care gaps, risk 3
    "P_DEMO_005": "snoozed",  # Linda Chen: active snooze
}


def find_patient(queue_data, patient_id):
    """
    Search all queue groups for a patient.
    """
    for queue_type in ["urgent", "routine", "snoozed"]:
        for item in queue_data[queue_type]:
            if item["patient_id"] == patient_id:
                return item

    return None


def validate_demo_patients():
    conn = connect_db()
    queue_data = get_ranked_queue_data(conn)
    conn.close()

    failures = []

    for patient_id, expected_queue_type in EXPECTED_QUEUE_TYPES.items():
        patient = find_patient(queue_data, patient_id)

        if patient is None:
            failures.append(
                f"{patient_id} was not found in any queue."
            )
            continue

        actual_queue_type = patient["queue_type"]

        if actual_queue_type != expected_queue_type:
            failures.append(
                f"{patient_id} expected '{expected_queue_type}' "
                f"but got '{actual_queue_type}'."
            )

    print("\n==============================")
    print("DEMO QUEUE VALIDATION")
    print("==============================")

    if failures:
        print("Validation failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("All expected demo patients are classified correctly.")

    for patient_id in EXPECTED_QUEUE_TYPES:
        patient = find_patient(queue_data, patient_id)
        print(
            f"- {patient_id}: {patient['patient_name']} "
            f"→ {patient['queue_type']} "
            f"| Reason: {patient['reason_surfaced']}"
        )


if __name__ == "__main__":
    validate_demo_patients()