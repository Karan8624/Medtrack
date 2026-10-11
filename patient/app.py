"""
MedTrack — Patient Interface

Run with:  streamlit run patient/app.py
(run it from the medtrack/ folder so the `shared` import resolves)

Restyled to match the MedTrack Patient Dashboard design (dark/light,
purple accent, card-based "Today" view with SOS, adherence and water
panels) while keeping all existing database-backed functionality.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta
import streamlit as st
from shared.auth import require_login, logout
from shared.db import run_query, run_write, get_mongo_db
from shared.queries import compute_adherence, auto_mark_missed_doses, todays_dose_queue, refill_due_soon
from shared.theme import inject_theme, theme_toggle, sidebar_profile, with_title

st.set_page_config(page_title="MedTrack — Patient", layout="wide")

# ---------------------------------------------------------------------------
# Theme (shared across patient/nurse/doctor — see shared/theme.py)
# ---------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"
inject_theme(st.session_state.theme)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
user = require_login("patient")
patient_id = user["patient_id"]
auto_mark_missed_doses()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔗 MedTrack")
    st.write("")
    section = st.radio(
        "Navigate",
        ["Today", "Medications", "Hydration", "Symptom journal", "Care team"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    theme_toggle()
    st.markdown("---")
    sidebar_profile(user, f"Patient · {user.get('age', '')}")
    if st.button("Log out"):
        logout()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
care_team = run_query(
    """
    SELECT d.name AS doctor_name, n.name AS nurse_name
    FROM patients p
    LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
    LEFT JOIN nurse_assignments na ON na.patient_id = p.patient_id
    LEFT JOIN nurses n ON na.nurse_id = n.nurse_id
    WHERE p.patient_id = %s
    """,
    (patient_id,),
)
care = care_team[0] if care_team else {"doctor_name": "—", "nurse_name": "—"}

doctor_display = with_title(care["doctor_name"], "Dr.")
nurse_display = with_title(care["nurse_name"], "Nurse")

top_l, top_r = st.columns([3, 2])
with top_l:
    st.markdown(f"<span class='muted'>{datetime.now().strftime('%A, %B %d · %I:%M %p')}</span>", unsafe_allow_html=True)
with top_r:
    st.markdown(
        f"<div style='text-align:right' class='muted'>{doctor_display} · {nurse_display}</div>",
        unsafe_allow_html=True,
    )

first_name = user["name"].split()[0]
hour = datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
st.markdown(f"## {greeting}, {first_name}")

# ---------------------------------------------------------------------------
# TODAY — main dashboard view
# ---------------------------------------------------------------------------
if section == "Today":
    main_col, side_col = st.columns([2, 1], gap="medium")

    with main_col:
        with st.container(border=True):
            st.markdown("<span class='eyebrow'>MEDICINE REMINDERS</span>", unsafe_allow_html=True)
            doses = todays_dose_queue(patient_id)
            taken_count = sum(1 for d in doses if d["status"] == "Taken")
            c1, c2 = st.columns([3, 1])
            c1.markdown("#### Today's doses")
            c2.markdown(f"<div style='text-align:right' class='muted'>{taken_count} of {len(doses)} taken</div>", unsafe_allow_html=True)
            st.progress(taken_count / len(doses) if doses else 0)

            if not doses:
                st.info("No doses scheduled for today.")
            for dose in doses:
                row_l, row_m, row_r = st.columns([2, 3, 2])
                with row_l:
                    st.write(dose["scheduled_time"].strftime("%I:%M %p"))
                with row_m:
                    st.write(f"**{dose['medicine']}** {dose['dosage']}")
                with row_r:
                    if dose["status"] == "Taken":
                        st.markdown("<span class='badge badge-green'>Taken</span>", unsafe_allow_html=True)
                    elif dose["status"] == "Missed":
                        st.markdown("<span class='badge badge-amber'>Missed</span>", unsafe_allow_html=True)
                        if st.button("I took it late", key=f"late_{dose['dose_id']}"):
                            run_write(
                                "UPDATE dose_log SET status='Taken', actual_time=%s WHERE dose_id=%s",
                                (datetime.now(), dose["dose_id"]),
                            )
                            st.rerun()
                    else:
                        due_now = dose["scheduled_time"] <= datetime.now()
                        label = "Mark taken" if not due_now else "✓ Mark taken"
                        if due_now:
                            st.markdown("<span class='badge badge-accent'>Due now</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span class='badge badge-neutral'>Upcoming</span>", unsafe_allow_html=True)
                        if st.button(label, key=f"take_{dose['dose_id']}"):
                            run_write(
                                "UPDATE dose_log SET status='Taken', actual_time=%s WHERE dose_id=%s",
                                (datetime.now(), dose["dose_id"]),
                            )
                            st.rerun()

            st.caption("Doses not marked within 60 minutes are logged as missed and shared with your nurse.")

            refills = refill_due_soon(patient_id)
            if refills:
                st.warning("Refill due soon: " + ", ".join(
                    f"{r['medicine']} (~{int(r['days_remaining'])} days left)" for r in refills
                ))

        st.write("")
        with st.container(border=True):
            st.markdown("<span class='eyebrow'>SYMPTOM JOURNAL</span>", unsafe_allow_html=True)
            st.markdown("#### How are you feeling?")
            mood = st.radio("Mood", ["Fine", "Okay", "Tired", "Anxious", "Unwell"], horizontal=True, label_visibility="collapsed")
            symptoms = st.multiselect(
                "Symptoms", ["Dizziness", "Headache", "Nausea", "Fatigue", "Mild pain"],
                label_visibility="collapsed",
            )
            note_col, btn_col = st.columns([4, 1])
            note = note_col.text_input("Add a note", placeholder="e.g. lightheaded after lunch", label_visibility="collapsed")
            if btn_col.button("Log entry"):
                db = get_mongo_db()
                db.symptom_journal.insert_one({
                    "patient_id": patient_id, "timestamp": datetime.now(),
                    "note": note, "severity": mood.lower(), "mood": mood.lower(), "tags": symptoms,
                })
                st.success("Entry saved.")

    with side_col:
        st.markdown(
            """
            <div class="sos-card">
                <h4>⚠ Need help now?</h4>
                <p>Alerts your nurse right away. For a life-threatening emergency, call your local emergency number.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        urgency = st.radio("How urgent is this?", ["Low", "Medium", "Urgent"], index=1, horizontal=True)
        sos_note = st.text_input("What's happening? (optional)")
        if st.button("🚨 Raise SOS", type="primary"):
            nurse_row = run_query("SELECT nurse_id FROM nurse_assignments WHERE patient_id = %s", (patient_id,))
            doctor_row = run_query("SELECT doctor_id FROM patients WHERE patient_id = %s", (patient_id,))
            if not nurse_row:
                st.error("No nurse is assigned to you yet — contact your doctor.")
            else:
                run_write(
                    """
                    INSERT INTO sos_complaints
                        (patient_id, nurse_id, doctor_id, description, severity, status, raised_at)
                    VALUES (%s, %s, %s, %s, %s, 'Raised', %s)
                    """,
                    (patient_id, nurse_row[0]["nurse_id"], doctor_row[0]["doctor_id"],
                     sos_note or "(no details provided)", urgency, datetime.now()),
                )
                st.success("SOS submitted — your nurse has been notified.")

        st.write("")
        with st.container(border=True):
            st.markdown("<span class='eyebrow'>ADHERENCE</span>", unsafe_allow_html=True)
            stats = compute_adherence(patient_id, days=7)
            st.markdown(f"# {stats['percent']}%")
            st.caption(f"this week · {stats['taken']} of {stats['total']} doses")

        st.write("")
        with st.container(border=True):
            st.markdown("<span class='eyebrow'>WATER INTAKE</span>", unsafe_allow_html=True)
            patient_row = run_query("SELECT water_target_ml FROM patients WHERE patient_id = %s", (patient_id,))[0]
            target = patient_row["water_target_ml"]
            db = get_mongo_db()
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_total = sum(
                e["amount_ml"] for e in db.water_log.find({"patient_id": patient_id, "timestamp": {"$gte": today_start}})
            )
            st.markdown(f"# {today_total} ml")
            remaining = max(target - today_total, 0)
            st.caption(f"Target {target} ml · {remaining} ml to go")
            st.progress(min(today_total / target, 1.0) if target else 0)
            q1, q2 = st.columns(2)
            if q1.button("+ 200 ml"):
                db.water_log.insert_one({"patient_id": patient_id, "timestamp": datetime.now(), "amount_ml": 200})
                st.rerun()
            if q2.button("+ 300 ml"):
                db.water_log.insert_one({"patient_id": patient_id, "timestamp": datetime.now(), "amount_ml": 300})
                st.rerun()

# ---------------------------------------------------------------------------
# MEDICATIONS
# ---------------------------------------------------------------------------
elif section == "Medications":
    st.markdown("#### Active prescriptions")
    prescriptions = run_query(
        """
        SELECT m.name AS medicine, p.dosage, p.frequency, p.remaining_qty, p.start_date, p.end_date
        FROM prescriptions p JOIN medicines m ON p.medicine_id = m.medicine_id
        WHERE p.patient_id = %s AND (p.end_date IS NULL OR p.end_date >= CURDATE())
        """,
        (patient_id,),
    )
    for rx in prescriptions:
        with st.container(border=True):
            st.write(f"**{rx['medicine']}** — {rx['dosage']}, {rx['frequency']}x/day")
            st.caption(f"{rx['remaining_qty']} remaining · started {rx['start_date']}")

# ---------------------------------------------------------------------------
# HYDRATION
# ---------------------------------------------------------------------------
elif section == "Hydration":
    st.markdown("#### Hydration history")
    db = get_mongo_db()
    entries = list(
        db.water_log.find({"patient_id": patient_id}).sort("timestamp", -1).limit(20)
    )
    for e in entries:
        st.write(f"{e['timestamp'].strftime('%b %d, %I:%M %p')} — {e['amount_ml']} ml")

# ---------------------------------------------------------------------------
# SYMPTOM JOURNAL (full history)
# ---------------------------------------------------------------------------
elif section == "Symptom journal":
    st.markdown("#### Journal history")
    db = get_mongo_db()
    entries = list(
        db.symptom_journal.find({"patient_id": patient_id}).sort("timestamp", -1).limit(20)
    )
    for e in entries:
        with st.container(border=True):
            st.write(f"**{e['timestamp'].strftime('%b %d, %I:%M %p')}** · {e.get('mood', '')}")
            if e.get("tags"):
                st.write(", ".join(e["tags"]))
            if e.get("note"):
                st.caption(e["note"])

# ---------------------------------------------------------------------------
# CARE TEAM
# ---------------------------------------------------------------------------
elif section == "Care team":
    st.markdown("#### Your care team")
    with st.container(border=True):
        st.write(f"**Doctor:** {doctor_display}")
    with st.container(border=True):
        st.write(f"**Nurse:** {nurse_display}")
