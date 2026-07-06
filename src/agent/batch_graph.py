import sys
from pathlib import Path
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph, START, END


CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[1]

sys.path.append(str(SRC_ROOT / "ranking"))
sys.path.append(str(SRC_ROOT / "context"))
sys.path.append(str(SRC_ROOT / "agent"))

from rank_queue import connect_db, get_ranked_queue_data
from assembler import assemble_patient_context
from brief_generator import generate_patient_brief, save_brief_to_notes


class A05BatchState(TypedDict, total=False):
    queue_data: Dict[str, Any]
    top_n: int
    selected_patients: List[Dict[str, Any]]
    processed_results: List[Dict[str, Any]]
    status: str
    trace: List[str]


def append_trace(state: A05BatchState, event: str) -> List[str]:
    existing_trace = state.get("trace", [])
    return existing_trace + [event]


def fetch_queue_node(state: A05BatchState) -> A05BatchState:
    conn = connect_db()
    queue_data = get_ranked_queue_data(conn)
    conn.close()

    return {
        "queue_data": queue_data,
        "status": "queue_fetched",
        "trace": append_trace(state, "fetch_queue: ranked queue retrieved"),
    }


def select_top_n_node(state: A05BatchState) -> A05BatchState:
    top_n = state.get("top_n", 3)
    urgent_queue = state["queue_data"]["urgent"]

    selected_patients = urgent_queue[:top_n]

    return {
        "selected_patients": selected_patients,
        "status": "patients_selected",
        "trace": append_trace(
            state,
            f"select_top_n: selected {len(selected_patients)} urgent patient(s)",
        ),
    }


def process_patients_node(state: A05BatchState) -> A05BatchState:
    selected_patients = state["selected_patients"]
    processed_results = []

    conn = connect_db()

    for patient in selected_patients:
        patient_id = patient["patient_id"]

        context = assemble_patient_context(conn, patient_id)
        brief = generate_patient_brief(context)
        save_brief_to_notes(conn, brief)

        processed_results.append(
            {
                "patient_id": patient_id,
                "patient_name": patient["patient_name"],
                "priority_score": patient["priority_score"],
                "reason_surfaced": patient["reason_surfaced"],
                "draft_saved": True,
                "escalation_required": brief["escalation"]["escalate"],
                "escalation_reasons": brief["escalation"]["reasons"],
            }
        )

    conn.close()

    return {
        "processed_results": processed_results,
        "status": "batch_complete",
        "trace": append_trace(
            state,
            f"process_patients: generated and saved {len(processed_results)} draft brief(s)",
        ),
    }


def build_batch_graph():
    graph = StateGraph(A05BatchState)

    graph.add_node("fetch_queue", fetch_queue_node)
    graph.add_node("select_top_n", select_top_n_node)
    graph.add_node("process_patients", process_patients_node)

    graph.add_edge(START, "fetch_queue")
    graph.add_edge("fetch_queue", "select_top_n")
    graph.add_edge("select_top_n", "process_patients")
    graph.add_edge("process_patients", END)

    return graph.compile()


def run_batch_graph(top_n=3):
    app = build_batch_graph()

    final_state = app.invoke(
        {
            "top_n": top_n,
            "trace": [],
        }
    )

    print("\n==============================")
    print("A05 BATCH LANGGRAPH RUN COMPLETE")
    print("==============================")
    print(f"Status: {final_state.get('status')}")

    print("\nGraph Trace")
    print("------------------------------")
    for index, event in enumerate(final_state.get("trace", []), start=1):
        print(f"{index}. {event}")

    print("\nProcessed Patients")
    print("------------------------------")

    for index, result in enumerate(final_state.get("processed_results", []), start=1):
        print(
            f"{index}. {result['patient_name']} "
            f"({result['patient_id']})"
        )
        print(f"   Priority score: {result['priority_score']}")
        print(f"   Reason surfaced: {result['reason_surfaced']}")
        print(f"   Draft saved: {result['draft_saved']}")
        print(f"   Escalation required: {result['escalation_required']}")

        if result["escalation_reasons"]:
            print("   Escalation reasons:")
            for reason in result["escalation_reasons"]:
                print(f"   - {reason}")

    print("\nDone.")


if __name__ == "__main__":
    run_batch_graph(top_n=3)