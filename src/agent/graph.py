import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import StateGraph, START, END

CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[1]

sys.path.append(str(SRC_ROOT / "ranking"))
sys.path.append(str(SRC_ROOT / "context"))
sys.path.append(str(SRC_ROOT / "agent"))

from rank_queue import connect_db, get_ranked_queue_data
from assembler import assemble_patient_context
from brief_generator import generate_patient_brief, save_brief_to_notes


class A05AgentState(TypedDict, total=False):
    """
    Shared state for the A05 Care Manager Agent graph.
    """
    queue_data: Dict[str, Any]
    selected_patient: Optional[Dict[str, Any]]
    patient_id: Optional[str]
    patient_context: Optional[Dict[str, Any]]
    brief: Optional[Dict[str, Any]]
    draft_saved: bool
    escalation_required: bool
    escalation_reasons: List[str]
    status: str
    error: Optional[str]


def fetch_queue_node(state: A05AgentState) -> A05AgentState:
    """
    Node 1:
    Fetch ranked urgent/routine/snoozed queue.
    """
    conn = connect_db()
    queue_data = get_ranked_queue_data(conn)
    conn.close()

    return {
        "queue_data": queue_data,
        "status": "queue_fetched"
    }


def select_top_urgent_node(state: A05AgentState) -> A05AgentState:
    """
    Node 2:
    Select top urgent patient from the active urgent queue.
    """
    queue_data = state["queue_data"]
    urgent_queue = queue_data["urgent"]

    if not urgent_queue:
        return {
            "selected_patient": None,
            "patient_id": None,
            "status": "no_urgent_patients"
        }

    selected_patient = urgent_queue[0]

    return {
        "selected_patient": selected_patient,
        "patient_id": selected_patient["patient_id"],
        "status": "patient_selected"
    }


def assemble_context_node(state: A05AgentState) -> A05AgentState:
    """
    Node 3:
    Assemble bounded patient context for the selected patient.
    """
    patient_id = state["patient_id"]

    conn = connect_db()
    patient_context = assemble_patient_context(conn, patient_id)
    conn.close()

    return {
        "patient_context": patient_context,
        "status": "context_assembled"
    }


def draft_brief_node(state: A05AgentState) -> A05AgentState:
    """
    Node 4:
    Generate unsigned AI-drafted patient brief.
    """
    patient_context = state["patient_context"]
    brief = generate_patient_brief(patient_context)

    escalation = brief["escalation"]

    return {
        "brief": brief,
        "escalation_required": escalation["escalate"],
        "escalation_reasons": escalation["reasons"],
        "status": "brief_drafted"
    }


def save_draft_node(state: A05AgentState) -> A05AgentState:
    """
    Node 5:
    Save unsigned AI-drafted brief into care_manager_notes.
    """
    brief = state["brief"]

    conn = connect_db()
    save_brief_to_notes(conn, brief)
    conn.close()

    return {
        "draft_saved": True,
        "status": "draft_saved_pending_human_review"
    }


def route_after_selection(state: A05AgentState) -> str:
    """
    Conditional edge:
    If no urgent patient exists, stop.
    Otherwise continue to context assembly.
    """
    if state.get("patient_id") is None:
        return "end"

    return "assemble_context"


def build_a05_graph():
    """
    Build and compile the A05 Care Manager Agent graph.
    """
    graph = StateGraph(A05AgentState)

    graph.add_node("fetch_queue", fetch_queue_node)
    graph.add_node("select_top_urgent", select_top_urgent_node)
    graph.add_node("assemble_context", assemble_context_node)
    graph.add_node("draft_brief", draft_brief_node)
    graph.add_node("save_draft", save_draft_node)

    graph.add_edge(START, "fetch_queue")
    graph.add_edge("fetch_queue", "select_top_urgent")

    graph.add_conditional_edges(
        "select_top_urgent",
        route_after_selection,
        {
            "assemble_context": "assemble_context",
            "end": END
        }
    )

    graph.add_edge("assemble_context", "draft_brief")
    graph.add_edge("draft_brief", "save_draft")
    graph.add_edge("save_draft", END)

    return graph.compile()


def run_graph():
    """
    Run the A05 agent graph once.
    """
    app = build_a05_graph()

    final_state = app.invoke({})

    print("\n==============================")
    print("A05 LANGGRAPH RUN COMPLETE")
    print("==============================")
    print(f"Status: {final_state.get('status')}")

    selected_patient = final_state.get("selected_patient")

    if selected_patient:
        print(
            f"Selected patient: "
            f"{selected_patient['patient_name']} "
            f"({selected_patient['patient_id']})"
        )
        print(f"Reason surfaced: {selected_patient['reason_surfaced']}")
        print(f"Draft saved: {final_state.get('draft_saved')}")
        print(f"Escalation required: {final_state.get('escalation_required')}")

        escalation_reasons = final_state.get("escalation_reasons", [])

        if escalation_reasons:
            print("Escalation reasons:")
            for reason in escalation_reasons:
                print(f"- {reason}")
    else:
        print("No urgent patients found.")


if __name__ == "__main__":
    run_graph()