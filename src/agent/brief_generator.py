import sys
from pathlib import Path

# Allow imports from src folders when running as a script
CURRENT_FILE = Path(__file__).resolve()
SRC_ROOT = CURRENT_FILE.parents[1]
sys.path.append(str(SRC_ROOT / "context"))

from assembler import connect_db, assemble_patient_context


def build_patient_summary(context):
    patient = context["patient"]
    risk = context["risk"]

    return (
        f"{patient['patient_name']} is an active attributed patient under "
        f"{patient['pcp_name']}. Current synthetic risk tier is "
        f"{risk['current_risk_tier']}, changed from baseline tier "
        f"{risk['baseline_risk_tier']}."
    )


def build_top_concerns(context):
    concerns = []

    risk = context["risk"]
    open_gaps = context["open_care_gaps"]
    encounters = context["recent_encounters"]
    medication_issues = context["medication_issues"]
    care_manager_notes = context["care_manager_notes"]

    if risk["current_risk_tier"] is not None and risk["current_risk_tier"] >= 4:
        concerns.append(
            f"Current risk tier is high: {risk['current_risk_tier']}."
        )

    if risk["risk_tier_delta"] is not None and risk["risk_tier_delta"] >= 2:
        concerns.append(
            f"Risk tier increased by {risk['risk_tier_delta']} levels from baseline."
        )

    recent_discharges = [
        encounter for encounter in encounters
        if encounter["discharge_flag"] == 1
    ]

    if recent_discharges:
        latest_discharge = recent_discharges[0]
        concerns.append(
            f"Recent discharge encounter on {latest_discharge['encounter_date']}."
        )

    if open_gaps:
        concerns.append(
            f"{len(open_gaps)} open care gap(s) require review."
        )

    if medication_issues:
        concerns.append(
            f"{len(medication_issues)} medication adherence issue(s) identified."
        )

    active_snoozes = [
        note for note in care_manager_notes
        if note["status"] == "snoozed" and note["snooze_until"]
    ]

    if active_snoozes:
        concerns.append(
            f"Patient has an active snooze until {active_snoozes[0]['snooze_until']}."
        )

    if not concerns:
        concerns.append("No major structured concerns identified in the bounded context.")

    return concerns[:5]


def build_suggested_actions(context):
    actions = []

    open_gaps = context["open_care_gaps"]
    encounters = context["recent_encounters"]
    medication_issues = context["medication_issues"]

    recent_discharges = [
        encounter for encounter in encounters
        if encounter["discharge_flag"] == 1
    ]

    if recent_discharges:
        actions.append("Review discharge summary and confirm follow-up plan is visible to the care team.")

    if open_gaps:
        actions.append("Review open care gaps and prioritize outreach for time-sensitive items.")

    if medication_issues:
        actions.append("Assess medication access, refill barriers, or adherence support needs.")

    actions.append("Document human review outcome before any note is finalized.")

    return actions


def check_escalation(context):
    """
    Deterministic escalation rule.

    The LLM should never decide escalation.
    This function uses structured fields only.
    """
    reasons = []

    risk = context["risk"]
    open_gaps = context["open_care_gaps"]
    encounters = context["recent_encounters"]

    if risk["current_risk_tier"] is not None and risk["current_risk_tier"] >= 4:
        reasons.append("Current risk tier is 4 or higher.")

    if risk["risk_tier_delta"] is not None and risk["risk_tier_delta"] >= 2:
        reasons.append("Risk tier increased by 2 or more levels from baseline.")

    for encounter in encounters:
        if encounter["discharge_flag"] == 1:
            reasons.append("Recent discharge encounter found in the assembled context.")
            break

    if len(open_gaps) >= 5:
        reasons.append("Five or more open care gaps found.")

    return {
        "escalate": len(reasons) > 0,
        "reasons": reasons
    }


def generate_patient_brief(context):
    escalation = check_escalation(context)

    return {
        "patient_id": context["patient"]["patient_id"],
        "patient_name": context["patient"]["patient_name"],
        "brief_status": "AI_DRAFT_UNSIGNED",
        "patient_summary": build_patient_summary(context),
        "top_concerns": build_top_concerns(context),
        "suggested_care_manager_actions": build_suggested_actions(context),
        "escalation": escalation,
        "disclaimer": (
            "AI-drafted care manager brief. This is unsigned, not clinician-reviewed, "
            "and must not be treated as a clinical decision or final documentation."
        )
    }


def print_patient_brief(brief):
    print("\n==============================")
    print("AI-DRAFTED PATIENT BRIEF")
    print("==============================")
    print(f"Patient: {brief['patient_name']} ({brief['patient_id']})")
    print(f"Status: {brief['brief_status']}")

    print("\nPatient Summary")
    print("------------------------------")
    print(brief["patient_summary"])

    print("\nTop Concerns")
    print("------------------------------")
    for concern in brief["top_concerns"]:
        print(f"- {concern}")

    print("\nSuggested Care Manager Actions")
    print("------------------------------")
    for action in brief["suggested_care_manager_actions"]:
        print(f"- {action}")

    print("\nEscalation")
    print("------------------------------")
    print(f"Escalate: {brief['escalation']['escalate']}")

    if brief["escalation"]["reasons"]:
        for reason in brief["escalation"]["reasons"]:
            print(f"- {reason}")
    else:
        print("- No escalation rule fired.")

    print("\nDisclaimer")
    print("------------------------------")
    print(brief["disclaimer"])


def main():
    conn = connect_db()

    patient_id = "P_DEMO_001"
    context = assemble_patient_context(conn, patient_id)
    brief = generate_patient_brief(context)

    conn.close()

    print_patient_brief(brief)


if __name__ == "__main__":
    main()