def check_escalation(context):
    """
    Deterministic escalation rules for A05.

    Important:
    - The LLM does not decide escalation.
    - This function uses only structured fields.
    - The output is auditable and testable.
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