import sqlite3
from pathlib import Path


DB_PATH = Path("data/a05_lpr.sqlite")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_ranked_queue(conn):
    """
    Build a deterministic ranked care manager queue.

    This uses structured SQL signals only:
    - current risk tier
    - risk tier change
    - open care gaps
    - recent discharge
    - medication adherence issues
    - snooze status
    """

    query = """
    WITH latest_risk AS (
        SELECT r1.patient_id, r1.risk_tier, r1.score_date
        FROM risk_scores r1
        WHERE r1.score_date = (
            SELECT MAX(r2.score_date)
            FROM risk_scores r2
            WHERE r2.patient_id = r1.patient_id
        )
    ),

    earliest_risk AS (
        SELECT r1.patient_id, r1.risk_tier, r1.score_date
        FROM risk_scores r1
        WHERE r1.score_date = (
            SELECT MIN(r2.score_date)
            FROM risk_scores r2
            WHERE r2.patient_id = r1.patient_id
        )
    ),

    gap_counts AS (
        SELECT
            patient_id,
            COUNT(*) AS open_gap_count
        FROM care_gaps
        WHERE status = 'open'
        GROUP BY patient_id
    ),

    recent_discharges AS (
        SELECT
            patient_id,
            MIN(julianday('now') - julianday(encounter_date)) AS days_since_discharge
        FROM encounters
        WHERE discharge_flag = 1
        GROUP BY patient_id
    ),

    medication_flags AS (
        SELECT
            patient_id,
            COUNT(*) AS adherence_issue_count
        FROM medication_events
        WHERE adherence_flag IN ('late_refill', 'missed_dose', 'non_adherent')
        GROUP BY patient_id
    ),

    active_snoozes AS (
        SELECT
            patient_id,
            MAX(snooze_until) AS snooze_until
        FROM care_manager_notes
        WHERE status = 'snoozed'
          AND snooze_until IS NOT NULL
          AND date(snooze_until) >= date('now')
        GROUP BY patient_id
    )

    SELECT
        p.patient_id,
        p.first_name || ' ' || p.last_name AS patient_name,
        p.pcp_name,

        lr.risk_tier AS current_risk_tier,
        er.risk_tier AS baseline_risk_tier,
        lr.risk_tier - er.risk_tier AS risk_tier_delta,

        COALESCE(gc.open_gap_count, 0) AS open_gap_count,
        COALESCE(rd.days_since_discharge, 999) AS days_since_discharge,
        COALESCE(mf.adherence_issue_count, 0) AS adherence_issue_count,

        CASE
            WHEN s.snooze_until IS NOT NULL THEN 1
            ELSE 0
        END AS is_snoozed,

        s.snooze_until,

        (
            lr.risk_tier * 0.40
            + COALESCE(gc.open_gap_count, 0) * 0.25
            + CASE
                WHEN COALESCE(rd.days_since_discharge, 999) <= 7 THEN 2.0
                WHEN COALESCE(rd.days_since_discharge, 999) <= 30 THEN 1.0
                ELSE 0
              END * 0.25
            + COALESCE(mf.adherence_issue_count, 0) * 0.10
            + CASE
                WHEN lr.risk_tier - er.risk_tier >= 2 THEN 1.0
                ELSE 0
              END
        ) AS priority_score,

        CASE
            WHEN s.snooze_until IS NOT NULL THEN 'snoozed'
            WHEN lr.risk_tier >= 4
              OR lr.risk_tier - er.risk_tier >= 2
              OR COALESCE(rd.days_since_discharge, 999) <= 7
            THEN 'urgent'
            ELSE 'routine'
        END AS queue_type

    FROM patients p
    JOIN latest_risk lr
        ON p.patient_id = lr.patient_id
    JOIN earliest_risk er
        ON p.patient_id = er.patient_id
    LEFT JOIN gap_counts gc
        ON p.patient_id = gc.patient_id
    LEFT JOIN recent_discharges rd
        ON p.patient_id = rd.patient_id
    LEFT JOIN medication_flags mf
        ON p.patient_id = mf.patient_id
    LEFT JOIN active_snoozes s
        ON p.patient_id = s.patient_id

    WHERE p.active = 1

    ORDER BY
        CASE
            WHEN s.snooze_until IS NOT NULL THEN 1
            ELSE 0
        END ASC,
        priority_score DESC;
    """

    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def print_queue(rows):
    urgent = [row for row in rows if row["queue_type"] == "urgent"]
    routine = [row for row in rows if row["queue_type"] == "routine"]
    snoozed = [row for row in rows if row["queue_type"] == "snoozed"]

    print("\n==============================")
    print("URGENT QUEUE")
    print("==============================")

    for index, row in enumerate(urgent[:10], start=1):
        print(
            f"{index}. {row['patient_name']} "
            f"| ID: {row['patient_id']} "
            f"| Score: {row['priority_score']:.2f} "
            f"| Risk: {row['current_risk_tier']} "
            f"| ΔRisk: {row['risk_tier_delta']} "
            f"| Open gaps: {row['open_gap_count']} "
            f"| Discharge days: {row['days_since_discharge']:.0f} "
            f"| Med issues: {row['adherence_issue_count']}"
        )

    print("\n==============================")
    print("ROUTINE QUEUE")
    print("==============================")

    for index, row in enumerate(routine[:10], start=1):
        print(
            f"{index}. {row['patient_name']} "
            f"| ID: {row['patient_id']} "
            f"| Score: {row['priority_score']:.2f} "
            f"| Risk: {row['current_risk_tier']} "
            f"| Open gaps: {row['open_gap_count']} "
            f"| Med issues: {row['adherence_issue_count']}"
        )

    print("\n==============================")
    print("SNOOZED")
    print("==============================")

    for index, row in enumerate(snoozed[:10], start=1):
        print(
            f"{index}. {row['patient_name']} "
            f"| ID: {row['patient_id']} "
            f"| Snoozed until: {row['snooze_until']} "
            f"| Score if active: {row['priority_score']:.2f}"
        )


def main():
    conn = connect_db()
    rows = get_ranked_queue(conn)
    conn.close()

    print_queue(rows)


if __name__ == "__main__":
    main()