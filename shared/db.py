"""
Shared database connection helpers for MedTrack.

Every page (patient/nurse/doctor) imports from this module instead of
opening its own MySQL or MongoDB connection. Centralizing it here means:
  - connection settings only need to change in one place
  - every query goes through the same parameterized-query helper,
    which protects against SQL injection
  - MongoDB access is one line (get_mongo_db()) instead of repeated
    boilerplate in every page

Usage example:

    from shared.db import run_query, run_write, get_mongo_db

    patients = run_query("SELECT * FROM patients WHERE doctor_id = %s", (doctor_id,))

    run_write(
        "UPDATE dose_log SET status = %s, actual_time = %s WHERE dose_id = %s",
        ("Taken", datetime.now(), dose_id),
    )

    db = get_mongo_db()
    db.water_log.insert_one({"patient_id": 12, "timestamp": datetime.now(), "amount_ml": 250})
"""

import os
import mysql.connector
from pymongo import MongoClient

MYSQL_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "localhost"),
    "user": os.environ.get("MYSQL_USER", "root"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "database": os.environ.get("MYSQL_DB", "medtrack"),
}
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")

_mongo_client = None  # created once, reused (avoids reconnecting on every call)


def get_mysql_connection():
    """Open a fresh MySQL connection using the configured credentials."""
    return mysql.connector.connect(**MYSQL_CONFIG)


def run_query(sql, params=None):
    """
    Run a SELECT and return the results as a list of dicts
    (so pages can do row["patient_id"] instead of row[0]).

    Always pass variable values via `params`, never by string-formatting
    them into `sql` — that's what keeps this safe from SQL injection.

    Example:
        rows = run_query("SELECT * FROM patients WHERE doctor_id = %s", (doctor_id,))
    """
    conn = get_mysql_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def run_write(sql, params=None):
    """
    Run an INSERT/UPDATE/DELETE. Returns the new row's id for an INSERT
    (lastrowid), or the number of affected rows for UPDATE/DELETE.

    Example:
        new_id = run_write(
            "INSERT INTO sos_complaints (patient_id, nurse_id, doctor_id, description, "
            "severity, raised_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (patient_id, nurse_id, doctor_id, description, severity, datetime.now()),
        )
    """
    conn = get_mysql_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    result = cur.lastrowid if cur.lastrowid else cur.rowcount
    cur.close()
    conn.close()
    return result


def get_mongo_db():
    """
    Return the 'medtrack' MongoDB database, reusing one client across calls.

    Example:
        db = get_mongo_db()
        db.symptom_journal.insert_one({...})
        entries = list(db.water_log.find({"patient_id": 12}))
    """
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI)
    return _mongo_client["medtrack"]
