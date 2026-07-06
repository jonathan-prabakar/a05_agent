import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"

sys.path.append(str(SRC_ROOT / "agent"))

from escalation import check_escalation


def test_escalates_for_high_risk_tier():
    context = {
        "risk": {
            "current_risk_tier": 4,
            "risk_tier_delta": 0
        },
        "open_care_gaps": [],
        "recent_encounters": []
    }

    result = check_escalation(context)

    assert result["escalate"] is True
    assert "Current risk tier is 4 or higher." in result["reasons"]


def test_escalates_for_risk_jump():
    context = {
        "risk": {
            "current_risk_tier": 3,
            "risk_tier_delta": 2
        },
        "open_care_gaps": [],
        "recent_encounters": []
    }

    result = check_escalation(context)

    assert result["escalate"] is True
    assert "Risk tier increased by 2 or more levels from baseline." in result["reasons"]


def test_escalates_for_recent_discharge():
    context = {
        "risk": {
            "current_risk_tier": 2,
            "risk_tier_delta": 0
        },
        "open_care_gaps": [],
        "recent_encounters": [
            {
                "discharge_flag": 1
            }
        ]
    }

    result = check_escalation(context)

    assert result["escalate"] is True
    assert "Recent discharge encounter found in the assembled context." in result["reasons"]


def test_escalates_for_many_open_gaps():
    context = {
        "risk": {
            "current_risk_tier": 2,
            "risk_tier_delta": 0
        },
        "open_care_gaps": [
            {}, {}, {}, {}, {}
        ],
        "recent_encounters": []
    }

    result = check_escalation(context)

    assert result["escalate"] is True
    assert "Five or more open care gaps found." in result["reasons"]


def test_does_not_escalate_for_low_risk_stable_patient():
    context = {
        "risk": {
            "current_risk_tier": 2,
            "risk_tier_delta": 0
        },
        "open_care_gaps": [
            {}
        ],
        "recent_encounters": []
    }

    result = check_escalation(context)

    assert result["escalate"] is False
    assert result["reasons"] == []