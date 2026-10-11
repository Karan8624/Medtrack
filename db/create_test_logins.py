"""
Sets a known password ("test1234") on one linked patient/nurse/doctor
trio, so you have accounts you can actually log in with while testing
the Streamlit apps — and so the SAME SOS/task/prescription flows show
up when you switch between those three test logins.

Earlier version of this script picked the first row of each table
independently, which could give you a test patient assigned to a
different nurse/doctor than the test nurse/doctor accounts — so an SOS
raised by the test patient never showed up in the test nurse's queue.
This version picks one patient who actually has both a doctor and a
nurse assigned, then sets the password on exactly that patient, that
nurse, and that doctor — so the three test accounts form one care team.

Run this once after seeding (safe to re-run any time).

Usage (from inside the medtrack/ folder, with your MYSQL_* env vars set):
    python db/create_test_logins.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import bcrypt
from shared.db import run_query, run_write

TEST_PASSWORD = "test1234"
hashed = bcrypt.hashpw(TEST_PASSWORD.encode(), bcrypt.gensalt()).decode()

# Find one patient that has both a doctor and a nurse assigned, so the
# three test accounts below are actually linked to each other.
linked = run_query(
    """
    SELECT p.patient_id, p.name AS patient_name, p.email AS patient_email,
           d.doctor_id, d.name AS doctor_name, d.email AS doctor_email,
           n.nurse_id, n.name AS nurse_name, n.email AS nurse_email
    FROM patients p
    JOIN doctors d ON p.doctor_id = d.doctor_id
    JOIN nurse_assignments na ON na.patient_id = p.patient_id
    JOIN nurses n ON na.nurse_id = n.nurse_id
    ORDER BY p.patient_id
    LIMIT 1
    """
)
if not linked:
    raise SystemExit(
        "No patient with both a doctor and a nurse assigned was found — "
        "re-run db/seed_data.py first."
    )
row = linked[0]

run_write("UPDATE patients SET password_hash = %s WHERE patient_id = %s", (hashed, row["patient_id"]))
run_write("UPDATE nurses SET password_hash = %s WHERE nurse_id = %s", (hashed, row["nurse_id"]))
run_write("UPDATE doctors SET password_hash = %s WHERE doctor_id = %s", (hashed, row["doctor_id"]))

print(f"Set password '{TEST_PASSWORD}' on one LINKED patient/nurse/doctor trio:\n")
print(f"  PATIENT  name: {row['patient_name']:20} email: {row['patient_email']:30} password: {TEST_PASSWORD}")
print(f"  NURSE    name: {row['nurse_name']:20} email: {row['nurse_email']:30} password: {TEST_PASSWORD}")
print(f"  DOCTOR   name: {row['doctor_name']:20} email: {row['doctor_email']:30} password: {TEST_PASSWORD}")
print(
    "\nThese three accounts share a care team — an SOS raised by this patient will show up "
    "in this nurse's queue, and once escalated, in this doctor's queue too."
)
