"""
MedTrack — Doctor Interface

Run with:  streamlit run doctor/app.py
(run it from the medtrack/ folder so the `shared` import resolves)

Restyled to match the MedTrack Doctor Dashboard design (dark/light, same
visual system as patient/nurse): a top stat row, a "Prescribe medication"
card with a live drug-interaction check (severe interactions require an
explicit acknowledgement before saving), an escalated-cases queue
(assign a nurse task or flag an in-person visit), and a patient adherence
overview sorted lowest-first with a <70% flag. All database-backed
functionality is unchanged from the original implementation.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, date, timedelta
import streamlit as st
from shared.auth import require_login, logout
from shared.db import run_query, run_write
from shared.queries import compute_adherence, check_drug_interactions
from shared.theme import inject_theme, theme_toggle, sidebar_profile, with_title

st.set_page_config(page_title="MedTrack — Doctor", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
inject_theme(st.session_state.theme)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
user = require_login("doctor")
doctor_id = user["doctor_id"]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔗 MedTrack")
    st.write("")
    section = st.radio(
        "Navigate",
        ["Overview", "Prescriptions", "Escalations", "Patients", "Nurses"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    theme_toggle()
    st.markdown("---")
    sidebar_profile(user, "Doctor")
    if st.button("Log out"):
        logout()

# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------
my_patients = run_query(
    "SELECT patient_id, name, age FROM patients WHERE doctor_id = %s ORDER BY name", (doctor_id,)
)
escalations = run_query(
    "SELECT COUNT(*) AS n FROM sos_complaints WHERE doctor_id = %s AND status = 'Escalated'", (doctor_id,)
)[0]["n"]
active_rx = run_query(
    """
    SELECT COUNT(*) AS n FROM prescriptions
    WHERE doctor_id = %s AND (end_date IS NULL OR end_date >= CURDATE())
    """,
    (doctor_id,),
)[0]["n"]

adherence_rows = []
for p in my_patients:
    stats = compute_adherence(p["patient_id"], days=7)
    meds = run_query(
        """
        SELECT m.name FROM prescriptions pr JOIN medicines m ON pr.medicine_id = m.medicine_id
        WHERE pr.patient_id = %s AND (pr.end_date IS NULL OR pr.end_date >= CURDATE())
        """,
        (p["patient_id"],),
    )
    adherence_rows.append({**p, **stats, "meds": ", ".join(m["name"] for m in meds)})
below_70 = sum(1 for r in adherence_rows if r["total"] and r["percent"] < 70)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
top_l, top_r = st.columns([3, 2])
with top_l:
    st.markdown(f"<span class='muted'>{datetime.now().strftime('%A, %B %d · %I:%M %p')}</span>", unsafe_allow_html=True)
with top_r:
    st.markdown(
        f"""
        <div class="stat-row">
            <div><div class="stat-num">{escalations}</div><div class="stat-label">escalations</div></div>
            <div><div class="stat-num">{below_70}</div><div class="stat-label">below 70%</div></div>
            <div><div class="stat-num">{active_rx}</div><div class="stat-label">active Rx</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

hour = datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
st.markdown(f"## {greeting}, {with_title(user['name'], 'Dr.')}")

SEVERITY_BADGE = {"Urgent": "badge-red", "Medium": "badge-amber", "Low": "badge-green"}
SEVERITY_ACCENT = {"Urgent": "left-accent-red", "Medium": "left-accent-amber", "Low": "left-accent-green"}


def render_prescribe_card():
    with st.container(border=True):
        st.markdown("<span class='eyebrow'>NEW PRESCRIPTION</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        c1.markdown("#### Prescribe medication")
        c2.markdown("<div style='text-align:right' class='muted'>Checked against active prescriptions</div>", unsafe_allow_html=True)

        if not my_patients:
            st.info("You have no patients assigned yet.")
            return

        pc1, pc2 = st.columns(2)
        patient_choice = pc1.selectbox("Patient", my_patients, format_func=lambda p: f"{p['name']} · {p['age']}")
        medicines = run_query("SELECT medicine_id, name FROM medicines ORDER BY name")
        medicine_choice = pc2.selectbox("Medicine", medicines, format_func=lambda m: m["name"])

        current_meds = run_query(
            """
            SELECT m.medicine_id, m.name FROM prescriptions pr JOIN medicines m ON pr.medicine_id = m.medicine_id
            WHERE pr.patient_id = %s AND (pr.end_date IS NULL OR pr.end_date >= CURDATE())
            """,
            (patient_choice["patient_id"],),
        )
        conflicts = check_drug_interactions(patient_choice["patient_id"], medicine_choice["medicine_id"])
        conflict_names = {c["existing_medicine"] for c in conflicts}

        if current_meds:
            st.caption("Currently taking")
            pill_html = ""
            for m in current_meds:
                cls = "badge-red" if m["name"] in conflict_names else "badge-neutral"
                pill_html += f"<span class='badge {cls}' style='margin-right:6px'>{m['name']}</span>"
            st.markdown(pill_html, unsafe_allow_html=True)

        dc1, dc2 = st.columns(2)
        dosage = dc1.text_input("Dosage (e.g. 25mg)")
        frequency = dc2.radio("Frequency", [1, 2, 3, 4], horizontal=True, format_func=lambda n: f"{n}× / day")
        quantity = st.number_input("Quantity dispensed", min_value=1, value=30)
        sc1, sc2 = st.columns(2)
        start = sc1.date_input("Start date", value=date.today())
        has_end = st.checkbox("Has an end date")
        end = sc2.date_input("End date", value=date.today() + timedelta(days=30)) if has_end else None

        can_create = True
        if conflicts:
            severe = any(c["severity"] == "Severe" for c in conflicts)
            lines = "<br>".join(f"{c['existing_medicine']} + {medicine_choice['name']}: {c['description']} · {c['severity']}" for c in conflicts)
            st.markdown(
                f"""
                <div class="sos-card" style="margin-bottom:8px">
                    <h4>⚠ Warning: interacts with existing prescription</h4>
                    <p>{lines}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if severe:
                ack = st.checkbox("I've reviewed this interaction and want to prescribe anyway", key="ack_interaction")
                can_create = ack
                st.caption("Severe interaction: confirm the review to continue.")

        bc1, bc2 = st.columns([1, 1])
        if bc1.button("Clear"):
            st.rerun()
        if bc2.button("Create prescription", type="primary", disabled=not can_create):
            run_write(
                """
                INSERT INTO prescriptions
                    (patient_id, doctor_id, medicine_id, dosage, frequency, quantity,
                     remaining_qty, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (patient_choice["patient_id"], doctor_id, medicine_choice["medicine_id"],
                 dosage, frequency, quantity, quantity, start, end),
            )
            st.success("Prescription saved.")
            st.rerun()


def get_escalated_cases():
    return run_query(
        """
        SELECT sc.sos_id, sc.description, sc.severity, sc.escalated_at, sc.resolution_notes,
               p.patient_id, p.name AS patient_name, p.age, na.nurse_id, n.name AS nurse_name
        FROM sos_complaints sc
        JOIN patients p ON sc.patient_id = p.patient_id
        JOIN nurse_assignments na ON na.patient_id = p.patient_id
        JOIN nurses n ON na.nurse_id = n.nurse_id
        WHERE sc.doctor_id = %s AND sc.status = 'Escalated'
        ORDER BY
            CASE sc.severity WHEN 'Urgent' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,
            sc.escalated_at ASC
        """,
        (doctor_id,),
    )


def render_escalated_card(case):
    accent_class = SEVERITY_ACCENT.get(case["severity"], "")
    badge_class = SEVERITY_BADGE.get(case["severity"], "badge-neutral")
    with st.container(border=True):
        st.markdown(f'<div class="{accent_class}" style="padding-left:10px">', unsafe_allow_html=True)
        head_l, head_r = st.columns([4, 2])
        with head_l:
            st.markdown(
                f"**{case['patient_name']}** &nbsp; {case['age']} &nbsp; <span class='badge {badge_class}'>{case['severity']}</span>",
                unsafe_allow_html=True,
            )
        with head_r:
            when = case["escalated_at"].strftime("%I:%M %p") if case.get("escalated_at") else ""
            st.markdown(f"<div style='text-align:right' class='muted'>Escalated {when} by {case['nurse_name']}</div>", unsafe_allow_html=True)
        st.write(case["description"])
        if case.get("resolution_notes"):
            st.caption(f"Nurse note: {case['resolution_notes']}")

        action = st.radio(
            "Action", ["Assign task to nurse", "Flag for in-person visit"],
            key=f"action_{case['sos_id']}", horizontal=True,
        )
        if action == "Assign task to nurse":
            task_type = st.selectbox(
                "Task type", ["Delivery", "Injection", "Procedure", "Other"],
                key=f"tasktype_{case['sos_id']}",
            )
            if st.button("📋 Assign task to nurse", key=f"assign_{case['sos_id']}"):
                run_write(
                    """
                    INSERT INTO tasks
                        (sos_id, patient_id, nurse_id, assigned_by_doctor_id,
                         task_type, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
                    """,
                    (case["sos_id"], case["patient_id"], case["nurse_id"], doctor_id,
                     task_type, datetime.now()),
                )
                run_write(
                    "UPDATE sos_complaints SET status = 'Doctor Reviewed', doctor_reviewed_at = %s WHERE sos_id = %s",
                    (datetime.now(), case["sos_id"]),
                )
                st.rerun()
        else:
            if st.button("🏠 Flag for in-person visit", key=f"inperson_{case['sos_id']}"):
                run_write(
                    """
                    UPDATE sos_complaints
                    SET status = 'Resolved (In-Person Required)', doctor_reviewed_at = %s, resolved_at = %s
                    WHERE sos_id = %s
                    """,
                    (datetime.now(), datetime.now(), case["sos_id"]),
                )
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_adherence_panel(sort_lowest_first=True):
    rows = sorted(adherence_rows, key=lambda r: r["percent"], reverse=not sort_lowest_first)
    if not rows:
        st.info("No patients assigned yet.")
    for r in rows:
        flag_class = "badge-amber" if r["total"] and r["percent"] < 70 else "badge-green"
        warn = "⚠ " if r["total"] and r["percent"] < 70 else ""
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0;">
                <div><b>{r['name']}</b><br><span class='muted'>{r['age']} · {r['meds'] or 'No active meds'}</span></div>
                <span class='badge {flag_class}'>{warn}{r['percent']}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------------------------
if section == "Overview":
    main_col, side_col = st.columns([2, 1], gap="medium")

    with main_col:
        render_prescribe_card()
        st.write("")
        st.markdown("<span class='eyebrow'>ESCALATED BY NURSES</span>", unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        c1.markdown("#### Cases to review")
        c2.markdown(f"<div style='text-align:right' class='muted'>{escalations} awaiting review</div>", unsafe_allow_html=True)
        cases = get_escalated_cases()
        if not cases:
            st.info("No escalated cases right now.")
        for case in cases:
            render_escalated_card(case)

    with side_col:
        st.markdown("<span class='eyebrow'>PATIENT OVERVIEW</span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### Adherence")
            render_adherence_panel()
            st.caption("Below 70% over 7 days is flagged amber.")

# ---------------------------------------------------------------------------
# PRESCRIPTIONS
# ---------------------------------------------------------------------------
elif section == "Prescriptions":
    render_prescribe_card()
    st.write("")
    st.markdown("#### Active prescriptions")
    rx = run_query(
        """
        SELECT p.name AS patient_name, m.name AS medicine, pr.dosage, pr.frequency, pr.remaining_qty, pr.start_date
        FROM prescriptions pr
        JOIN patients p ON pr.patient_id = p.patient_id
        JOIN medicines m ON pr.medicine_id = m.medicine_id
        WHERE pr.doctor_id = %s AND (pr.end_date IS NULL OR pr.end_date >= CURDATE())
        ORDER BY pr.start_date DESC
        """,
        (doctor_id,),
    )
    for r in rx:
        with st.container(border=True):
            st.write(f"**{r['medicine']}** for {r['patient_name']} — {r['dosage']}, {r['frequency']}x/day")
            st.caption(f"{r['remaining_qty']} remaining · started {r['start_date']}")

# ---------------------------------------------------------------------------
# ESCALATIONS
# ---------------------------------------------------------------------------
elif section == "Escalations":
    st.markdown("#### Cases escalated by nurses")
    cases = get_escalated_cases()
    if not cases:
        st.info("No escalated cases right now.")
    for case in cases:
        render_escalated_card(case)

# ---------------------------------------------------------------------------
# PATIENTS
# ---------------------------------------------------------------------------
elif section == "Patients":
    st.markdown("#### Adherence overview")
    sort_choice = st.radio("Sort", ["Lowest first", "Highest first"], horizontal=True, label_visibility="collapsed")
    render_adherence_panel(sort_lowest_first=(sort_choice == "Lowest first"))

# ---------------------------------------------------------------------------
# NURSES
# ---------------------------------------------------------------------------
elif section == "Nurses":
    st.markdown("#### Nurses assigned to your patients")
    nurses = run_query(
        """
        SELECT DISTINCT n.nurse_id, n.name, COUNT(na.patient_id) AS patient_count
        FROM nurses n
        JOIN nurse_assignments na ON na.nurse_id = n.nurse_id
        JOIN patients p ON na.patient_id = p.patient_id
        WHERE p.doctor_id = %s
        GROUP BY n.nurse_id, n.name
        ORDER BY n.name
        """,
        (doctor_id,),
    )
    if not nurses:
        st.info("No nurses are currently covering your patients.")
    for n in nurses:
        with st.container(border=True):
            st.write(f"**{n['name']}** — covering {n['patient_count']} of your patients")
