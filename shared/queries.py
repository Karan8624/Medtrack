"""
Shared "advanced query" logic used by more than one interface.

Putting these here (instead of writing the same SQL three times across
patient/nurse/doctor) means:
  - the adherence % calculation is identical everywhere it's shown
  - the drug-interaction check only needs to be gotten right once
  - these are also the functions worth pointing to directly when writing
    up the "Advanced Database Querying" section of the report
"""

from datetime import datetime, timedelta
from shared.db import run_query, run_write


def compute_adherence(patient_id: int, days: int = 7) -> dict:
    """
    % of scheduled doses actually taken for this patient over the last
    `days` days. Returns {"taken": n, "total": n, "percent": float}.
    """
    since = datetime.now() - timedelta(days=days)
    rows = run_query(
        """
        SELECT dl.status
        FROM dose_log dl
        JOIN prescriptions p ON dl.prescription_id = p.prescription_id
        WHERE p.patient_id = %s AND dl.scheduled_time >= %s
        """,
        (patient_id, since),
    )
    total = len(rows)
    taken = sum(1 for r in rows if r["status"] == "Taken")
    percent = round((taken / total) * 100, 1) if total else 0.0
    return {"taken": taken, "total": total, "percent": percent}


def check_drug_interactions(patient_id: int, new_medicine_id: int) -> list:
    """
    Check a prospective new medicine against the patient's currently
    active prescriptions. Returns a list of dicts describing any
    conflicts found (empty list = no conflicts).
    """
    return run_query(
        """
        SELECT m.name AS existing_medicine, di.severity, di.description
        FROM prescriptions p
        JOIN medicines m ON p.medicine_id = m.medicine_id
        JOIN drug_interactions di
          ON (di.medicine_id_a = p.medicine_id AND di.medicine_id_b = %s)
          OR (di.medicine_id_b = p.medicine_id AND di.medicine_id_a = %s)
        WHERE p.patient_id = %s
          AND (p.end_date IS NULL OR p.end_date >= CURDATE())
        """,
        (new_medicine_id, new_medicine_id, patient_id),
    )


def refill_due_soon(patient_id: int, days_threshold: int = 5) -> list:
    """
    Prescriptions for this patient where remaining_qty will run out
    within `days_threshold` days, based on frequency (doses/day).
    """
    return run_query(
        """
        SELECT p.prescription_id, m.name AS medicine, p.remaining_qty, p.frequency,
               (p.remaining_qty / p.frequency) AS days_remaining
        FROM prescriptions p
        JOIN medicines m ON p.medicine_id = m.medicine_id
        WHERE p.patient_id = %s
          AND (p.remaining_qty / p.frequency) <= %s
        ORDER BY days_remaining ASC
        """,
        (patient_id, days_threshold),
    )


def auto_mark_missed_doses(grace_minutes: int = 60):
    """
    Mark any dose_log row as 'Missed' if its scheduled_time is more than
    `grace_minutes` in the past and it's still 'Pending'. Call this once
    near the top of any page that displays reminders, so the view is
    always current. Returns the number of rows updated.
    """
    cutoff = datetime.now() - timedelta(minutes=grace_minutes)
    return run_write(
        """
        UPDATE dose_log
        SET status = 'Missed'
        WHERE status = 'Pending' AND scheduled_time < %s
        """,
        (cutoff,),
    )


def todays_dose_queue(patient_id: int) -> list:
    """Today's scheduled doses for a patient, earliest first."""
    return run_query(
        """
        SELECT dl.dose_id, dl.scheduled_time, dl.status, m.name AS medicine, p.dosage
        FROM dose_log dl
        JOIN prescriptions p ON dl.prescription_id = p.prescription_id
        JOIN medicines m ON p.medicine_id = m.medicine_id
        WHERE p.patient_id = %s AND DATE(dl.scheduled_time) = CURDATE()
        ORDER BY dl.scheduled_time ASC
        """,
        (patient_id,),
    )
