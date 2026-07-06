import sys
from pathlib import Path

CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[1]

sys.path.append(str(SRC_ROOT / "ranking"))
sys.path.append(str(SRC_ROOT / "context"))
sys.path.append(str(SRC_ROOT / "agent"))

from rank_queue import connect_db, get_ranked_queue_data
from assembler import assemble_patient_context
from brief_generator import generate_patient_brief, save_brief_to_notes


def run_agent_sweep(top_n=3):
    """
    Run a simple automated A05 care manager agent sweep.

    This is not LangGraph yet.
    This proves the full automated backend loop:
    queue -> context -> brief -> save draft -> escalation visibility.
    """
    conn = connect_db()

    queue_data = get_ranked_queue_data(conn)
    urgent_patients = queue_data["urgent"][:top_n]

    print("\n==============================")
    print("A05 SIMPLE AGENT SWEEP")
    print("==============================")
    print(f"Total urgent patients: {queue_data['urgent_count']}")
    print(f"Processing top {len(urgent_patients)} urgent patient(s).")

    for index, patient in enumerate(urgent_patients, start=1):
        patient_id = patient["patient_id"]

        print("\n------------------------------")
        print(f"{index}. Processing {patient['patient_name']} ({patient_id})")
        print("------------------------------")
        print(f"Priority score: {patient['priority_score']}")
        print(f"Reason surfaced: {patient['reason_surfaced']}")

        context = assemble_patient_context(conn, patient_id)
        brief = generate_patient_brief(context)

        save_brief_to_notes(conn, brief)

        print(f"Draft saved for: {brief['patient_name']}")
        print(f"Escalate: {brief['escalation']['escalate']}")

        if brief["escalation"]["reasons"]:
            print("Escalation reasons:")
            for reason in brief["escalation"]["reasons"]:
                print(f"- {reason}")

    conn.close()

    print("\n==============================")
    print("AGENT SWEEP COMPLETE")
    print("==============================")


if __name__ == "__main__":
    run_agent_sweep(top_n=3)