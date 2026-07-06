import sys
from pathlib import Path

import streamlit as st


CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

sys.path.append(str(SRC_ROOT / "ranking"))

from rank_queue import connect_db, get_ranked_queue_data


st.set_page_config(
    page_title="A05 Care Manager Agent",
    page_icon="🩺",
    layout="wide"
)


def load_queue_data():
    conn = connect_db()
    queue_data = get_ranked_queue_data(conn)
    conn.close()
    return queue_data


def render_queue_table(queue_items, queue_name):
    if not queue_items:
        st.info(f"No patients in {queue_name} queue.")
        return

    for patient in queue_items:
        with st.container(border=True):
            left_col, right_col = st.columns([3, 1])

            with left_col:
                st.subheader(patient["patient_name"])
                st.caption(f"Patient ID: {patient['patient_id']}")
                st.write(patient["reason_surfaced"])

            with right_col:
                st.metric("Priority Score", patient["priority_score"])
                st.write(f"Risk Tier: **{patient['current_risk_tier']}**")
                st.write(f"Queue: **{patient['queue_type']}**")


def main():
    st.title("A05 Care Manager Agent")
    st.caption(
        "Prioritized queue, bounded patient context, and AI-drafted care manager documentation."
    )

    queue_data = load_queue_data()

    summary_col_1, summary_col_2, summary_col_3, summary_col_4 = st.columns(4)

    with summary_col_1:
        st.metric("Total Active Patients", queue_data["total_count"])

    with summary_col_2:
        st.metric("Urgent", queue_data["urgent_count"])

    with summary_col_3:
        st.metric("Routine", queue_data["routine_count"])

    with summary_col_4:
        st.metric("Snoozed", queue_data["snoozed_count"])

    st.divider()

    urgent_tab, routine_tab, snoozed_tab = st.tabs(
        ["Urgent Queue", "Routine Queue", "Snoozed"]
    )

    with urgent_tab:
        st.header("Urgent Queue")
        st.caption("Patients surfaced by deterministic structured rules.")
        render_queue_table(queue_data["urgent"][:15], "urgent")

    with routine_tab:
        st.header("Routine Queue")
        st.caption("Patients requiring follow-up but not currently urgent.")
        render_queue_table(queue_data["routine"][:15], "routine")

    with snoozed_tab:
        st.header("Snoozed")
        st.caption("Patients temporarily suppressed from the active queue.")
        render_queue_table(queue_data["snoozed"][:15], "snoozed")


if __name__ == "__main__":
    main()