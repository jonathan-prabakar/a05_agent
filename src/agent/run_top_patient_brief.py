import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[1]

sys.path.append(str(SRC_ROOT / "ranking"))
sys.path.append(str(SRC_ROOT / "context"))
sys.path.append(str(SRC_ROOT / "agent"))

from rank_queue import connect_db as connect_ranking_db
from rank_queue import get_ranked_queue_data

from assembler import assemble_patient_context

from brief_generator import (
    generate_patient_brief,
    save_brief_to_notes,
    print_patient_brief,
)


def select_top_urgent_patient(queue_data):
    """
    Select the highest-priority active urgent patient.

    Snoozed patients are intentionally excluded because they are not
    part of the active urgent queue.
    """
    urgent_queue = queue_data["urgent"]

    if not urgent_queue:
        return None

    return urgent_queue[0]


def run_top_patient_brief():
    """
    Run the core A05 flow for the top urgent patient:

    ranked queue -> selected patient -> context -> draft brief -> saved note
    """
    conn = connect_ranking_db()

    queue_data = get_ranked_queue_data(conn)
    top_patient = select_top_urgent_patient(queue_data)

    if top_patient is None:
        conn.close()
        print("No urgent patients found.")
        return

    patient_id = top_patient["patient_id"]

    print("\n==============================")
    print("TOP URGENT PATIENT SELECTED")
    print("==============================")
    print(f"Patient: {top_patient['patient_name']} ({patient_id})")
    print(f"Priority score: {top_patient['priority_score']}")
    print(f"Reason surfaced: {top_patient['reason_surfaced']}")

    context = assemble_patient_context(conn, patient_id)
    brief = generate_patient_brief(context)

    save_brief_to_notes(conn, brief)

    conn.close()

    print_patient_brief(brief)


if __name__ == "__main__":
    run_top_patient_brief()