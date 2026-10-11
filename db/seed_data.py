"""
MedTrack seed data generator.

Generates fake but realistic-looking data for all SQL tables and both
MongoDB collections, so the rest of the team has something to build
against immediately.

Usage:
    pip install faker mysql-connector-python pymongo bcrypt
    python seed_data.py

Set your connection details via environment variables (or edit the
CONFIG block below) before running:
    MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
    MONGO_URI

This script is intentionally simple and readable over clever — it's
meant to be something any of you can open and tweak (e.g. change how
many patients, add a medicine) without needing to understand the
whole codebase.
"""

import os
import random
import datetime as dt

from faker import Faker
import bcrypt

fake = Faker()
random.seed(42)  # reproducible fake data across the team

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

NUM_DOCTORS = 4
NUM_NURSES = 5
NUM_PATIENTS = 25
DAYS_OF_DOSE_HISTORY = 21  # ~3 weeks, enough for adherence trends to show

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DB", "medtrack"),
}
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

# Real, cited drug interaction pairs (see SRS section 5a for sources)
MEDICINES = [
    "Warfarin", "Aspirin", "Ibuprofen", "Amoxicillin", "Lisinopril",
    "Spironolactone", "Simvastatin", "Erythromycin", "Phenelzine",
    "Fluoxetine", "Metformin", "Digoxin", "Furosemide", "Sildenafil",
    "Nitroglycerin", "Methotrexate", "Diazepam", "Morphine",
    "Paracetamol", "Cetirizine",
]

INTERACTIONS = [
    ("Warfarin", "Aspirin", "Severe", "Increased bleeding risk"),
    ("Warfarin", "Ibuprofen", "Severe", "Increased bleeding risk"),
    ("Warfarin", "Amoxicillin", "Moderate", "Enhanced anticoagulant effect"),
    ("Lisinopril", "Spironolactone", "Severe", "Hyperkalemia"),
    ("Simvastatin", "Erythromycin", "Severe", "Increased risk of muscle toxicity"),
    ("Phenelzine", "Fluoxetine", "Severe", "Serotonin syndrome"),
    ("Digoxin", "Furosemide", "Moderate", "Electrolyte imbalance increasing digoxin toxicity"),
    ("Sildenafil", "Nitroglycerin", "Severe", "Severe hypotension"),
    ("Methotrexate", "Ibuprofen", "Moderate", "Increased methotrexate toxicity"),
    ("Diazepam", "Morphine", "Severe", "Respiratory depression risk"),
]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def build_mysql():
    import mysql.connector

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    # --- doctors ---
    doctor_ids = []
    for _ in range(NUM_DOCTORS):
        cur.execute(
            "INSERT INTO doctors (name, specialization, email, password_hash) "
            "VALUES (%s, %s, %s, %s)",
            (
                f"Dr. {fake.last_name()}",
                random.choice(["General Medicine", "Cardiology", "Internal Medicine", "Geriatrics"]),
                fake.unique.email(),
                hash_password("password123"),
            ),
        )
        doctor_ids.append(cur.lastrowid)

    # --- nurses ---
    nurse_ids = []
    for _ in range(NUM_NURSES):
        cur.execute(
            "INSERT INTO nurses (name, email, password_hash) VALUES (%s, %s, %s)",
            (fake.name(), fake.unique.email(), hash_password("password123")),
        )
        nurse_ids.append(cur.lastrowid)

    # --- medicines ---
    medicine_ids = {}
    for name in MEDICINES:
        cur.execute("INSERT INTO medicines (name) VALUES (%s)", (name,))
        medicine_ids[name] = cur.lastrowid

    # --- drug_interactions ---
    for med_a, med_b, severity, desc in INTERACTIONS:
        cur.execute(
            "INSERT INTO drug_interactions (medicine_id_a, medicine_id_b, severity, description) "
            "VALUES (%s, %s, %s, %s)",
            (medicine_ids[med_a], medicine_ids[med_b], severity, desc),
        )

    # --- patients + nurse_assignments ---
    patient_ids = []
    for _ in range(NUM_PATIENTS):
        doctor_id = random.choice(doctor_ids)
        cur.execute(
            "INSERT INTO patients (name, age, gender, weight_kg, email, password_hash, "
            "water_target_ml, doctor_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (
                fake.name(),
                random.randint(22, 85),
                random.choice(["Male", "Female", "Other"]),
                round(random.uniform(50, 95), 1),
                fake.unique.email(),
                hash_password("password123"),
                random.choice([1800, 2000, 2200, 2500]),
                doctor_id,
            ),
        )
        pid = cur.lastrowid
        patient_ids.append(pid)

        nurse_id = random.choice(nurse_ids)
        cur.execute(
            "INSERT INTO nurse_assignments (patient_id, nurse_id, assigned_date) VALUES (%s, %s, %s)",
            (pid, nurse_id, fake.date_between(start_date="-60d", end_date="-30d")),
        )

    # --- prescriptions + dose_log ---
    today = dt.date.today()
    for pid in patient_ids:
        doctor_id = random.choice(doctor_ids)
        num_prescriptions = random.randint(1, 3)
        chosen_meds = random.sample(MEDICINES, num_prescriptions)

        for med_name in chosen_meds:
            frequency = random.choice([1, 2, 3])  # doses per day
            quantity = frequency * 30
            start_date = today - dt.timedelta(days=DAYS_OF_DOSE_HISTORY)
            cur.execute(
                "INSERT INTO prescriptions (patient_id, doctor_id, medicine_id, dosage, "
                "frequency, quantity, remaining_qty, start_date, end_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    pid, doctor_id, medicine_ids[med_name],
                    f"{random.choice([250, 500, 650])}mg",
                    frequency, quantity, quantity, start_date, None,
                ),
            )
            prescription_id = cur.lastrowid

            # generate dose_log history for this prescription
            for day_offset in range(DAYS_OF_DOSE_HISTORY):
                log_date = start_date + dt.timedelta(days=day_offset)
                for dose_num in range(frequency):
                    hour = [8, 14, 20][dose_num] if frequency <= 3 else 8 + dose_num * (12 // frequency)
                    scheduled = dt.datetime.combine(log_date, dt.time(hour=hour))
                    # ~85% adherence, with some randomness so trends look real
                    taken = random.random() < 0.85
                    if scheduled > dt.datetime.now():
                        status, actual = "Pending", None
                    elif taken:
                        status = "Taken"
                        actual = scheduled + dt.timedelta(minutes=random.randint(-10, 45))
                    else:
                        status, actual = "Missed", None
                    cur.execute(
                        "INSERT INTO dose_log (prescription_id, scheduled_time, actual_time, status) "
                        "VALUES (%s, %s, %s, %s)",
                        (prescription_id, scheduled, actual, status),
                    )

    # --- a few sample SOS complaints + tasks, for demo purposes ---
    for _ in range(8):
        pid = random.choice(patient_ids)
        cur.execute(
            "SELECT nurse_id FROM nurse_assignments WHERE patient_id = %s", (pid,)
        )
        nurse_id = cur.fetchone()[0]
        cur.execute("SELECT doctor_id FROM patients WHERE patient_id = %s", (pid,))
        doctor_id = cur.fetchone()[0]

        raised_at = fake.date_time_between(start_date="-14d", end_date="now")
        escalate = random.random() < 0.4
        status = "Escalated" if escalate else "Self-Resolved"
        cur.execute(
            "INSERT INTO sos_complaints (patient_id, nurse_id, doctor_id, description, "
            "severity, status, raised_at, nurse_reviewed_at, escalated_at, resolution_notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                pid, nurse_id, doctor_id,
                random.choice([
                    "Ran out of medicine, need a refill delivered",
                    "Feeling dizzy since this morning",
                    "Mild fever and headache",
                    "Missed two doses, feeling anxious about it",
                ]),
                random.choice(["Low", "Medium", "Urgent"]),
                status,
                raised_at,
                raised_at + dt.timedelta(hours=1),
                raised_at + dt.timedelta(hours=2) if escalate else None,
                None if escalate else "Delivered replacement medicine, patient stable.",
            ),
        )
        sos_id = cur.lastrowid

        if escalate:
            cur.execute(
                "INSERT INTO tasks (sos_id, patient_id, nurse_id, assigned_by_doctor_id, "
                "task_type, status, notes, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (
                    sos_id, pid, nurse_id, doctor_id,
                    random.choice(["Delivery", "Injection", "Procedure"]),
                    random.choice(["Pending", "In Progress", "Completed"]),
                    "Auto-generated demo task.",
                    raised_at + dt.timedelta(hours=3),
                ),
            )

    conn.commit()
    cur.close()
    conn.close()
    print(f"MySQL seed complete: {NUM_DOCTORS} doctors, {NUM_NURSES} nurses, "
          f"{NUM_PATIENTS} patients, {len(MEDICINES)} medicines, "
          f"{len(INTERACTIONS)} interaction pairs.")


def build_mongo():
    from pymongo import MongoClient

    client = MongoClient(MONGO_URI)
    db = client["medtrack"]

    db.symptom_journal.delete_many({})
    db.water_log.delete_many({})

    symptom_tags = ["dizziness", "headache", "nausea", "fatigue", "mild pain"]
    moods = ["fine", "tired", "anxious", "okay", "unwell"]

    journal_docs = []
    water_docs = []
    now = dt.datetime.now()

    for pid in range(1, NUM_PATIENTS + 1):
        for day_offset in range(DAYS_OF_DOSE_HISTORY):
            day = now - dt.timedelta(days=day_offset)

            # occasional symptom journal entry (not every day, on purpose —
            # this is exactly why it's a flexible-shape MongoDB doc)
            if random.random() < 0.3:
                journal_docs.append({
                    "patient_id": pid,
                    "timestamp": day.replace(hour=random.randint(8, 22)),
                    "note": fake.sentence(nb_words=8),
                    "tags": random.sample(symptom_tags, k=random.randint(1, 2)),
                    "severity": random.choice(["mild", "moderate"]),
                    "mood": random.choice(moods),
                })

            # a few water log entries per day
            for _ in range(random.randint(2, 5)):
                water_docs.append({
                    "patient_id": pid,
                    "timestamp": day.replace(hour=random.randint(7, 22)),
                    "amount_ml": random.choice([150, 200, 250, 300]),
                })

    if journal_docs:
        db.symptom_journal.insert_many(journal_docs)
    if water_docs:
        db.water_log.insert_many(water_docs)

    print(f"MongoDB seed complete: {len(journal_docs)} symptom journal entries, "
          f"{len(water_docs)} water log entries.")


if __name__ == "__main__":
    build_mysql()
    build_mongo()
    print("\nDone. Both databases are seeded and ready to build against.")
