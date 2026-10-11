"""
MedTrack — Nurse Interface

Run with:  streamlit run nurse/app.py
(run it from the medtrack/ folder so the `shared` import resolves)

Restyled to match the MedTrack Nurse Dashboard design (dark/light, same
visual system as the patient app): a top stat row, an incoming
SOS/complaints queue sorted by severity with self-resolve / escalate
actions, a tasks list with status filters, and a patient case-load panel
with 7-day adherence flagged amber under 70%. All database-backed
functionality is unchanged from the original implementation.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime
import streamlit as st
from shared.auth import require_login, logout
from shared.db import run_query, run_write
from shared.queries import compute_adherence
from shared.theme import inject_theme, theme_toggle, sidebar_profile, with_title

st.set_page_config(page_title="MedTrack — Nurse", layout="wide")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
inject_theme(st.session_state.theme)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
user = require_login("nurse")
nurse_id = user["nurse_id"]

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔗 MedTrack")
    st.write("")
    section = st.radio(
        "Navigate",
        ["Overview", "SOS queue", "Tasks", "My patients"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    theme_toggle()
    st.markdown("---")
    sidebar_profile(user, "Nurse")
    if st.button("Log out"):
        logout()

# ---------------------------------------------------------------------------
# Shared data for header stats + panels
# ---------------------------------------------------------------------------
open_sos = run_query(
    "SELECT COUNT(*) AS n FROM sos_complaints WHERE nurse_id = %s AND status IN ('Raised', 'Under Nurse Review')",
    (nurse_id,),
)[0]["n"]
tasks_left = run_query(
    "SELECT COUNT(*) AS n FROM tasks WHERE nurse_id = %s AND status != 'Completed'",
    (nurse_id,),
)[0]["n"]
patients = run_query(
    """
    SELECT p.patient_id, p.name, p.age, p.gender, d.name AS doctor_name
    FROM nurse_assignments na
    JOIN patients p ON na.patient_id = p.patient_id
    LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
    WHERE na.nurse_id = %s
    ORDER BY p.name
    """,
    (nurse_id,),
)

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
            <div><div class="stat-num">{open_sos}</div><div class="stat-label">open SOS</div></div>
            <div><div class="stat-num">{tasks_left}</div><div class="stat-label">tasks left</div></div>
            <div><div class="stat-num">{len(patients)}</div><div class="stat-label">patients</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

first_name = user["name"].split()[0]
hour = datetime.now().hour
greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")
st.markdown(f"## {greeting}, {first_name}")

SEVERITY_BADGE = {"Urgent": "badge-red", "Medium": "badge-amber", "Low": "badge-green"}
SEVERITY_ACCENT = {"Urgent": "left-accent-red", "Medium": "left-accent-amber", "Low": "left-accent-green"}
TASK_BADGE = {"Pending": "badge-neutral", "In Progress": "badge-accent", "Completed": "badge-green"}


def render_sos_card(case, show_status_filter_context=False):
    accent_class = SEVERITY_ACCENT.get(case["severity"], "")
    badge_class = SEVERITY_BADGE.get(case["severity"], "badge-neutral")
    with st.container(border=True):
        st.markdown(f'<div class="{accent_class}" style="padding-left:10px">', unsafe_allow_html=True)
        head_l, head_r = st.columns([4, 1])
        with head_l:
            st.markdown(
                f"**{case['patient_name']}** &nbsp; {case['age']} · {with_title(case.get('doctor_name', ''), 'Dr.')}"
                f" &nbsp; <span class='badge {badge_class}'>{case['severity']}</span>",
                unsafe_allow_html=True,
            )
        with head_r:
            raised_ago = case["raised_at"].strftime("%I:%M %p") if case.get("raised_at") else ""
            st.markdown(f"<div style='text-align:right' class='muted'>{raised_ago}</div>", unsafe_allow_html=True)
        st.write(case["description"])
        st.caption(case["status"])

        col1, col2 = st.columns(2)
        with col1:
            notes = st.text_input("Resolution notes", key=f"notes_{case['sos_id']}", label_visibility="collapsed", placeholder="Resolution notes (optional)")
            if st.button("✓ Self-Resolve", key=f"resolve_{case['sos_id']}"):
                run_write(
                    """
                    UPDATE sos_complaints
                    SET status = 'Self-Resolved', nurse_reviewed_at = %s, resolution_notes = %s
                    WHERE sos_id = %s
                    """,
                    (datetime.now(), notes, case["sos_id"]),
                )
                st.rerun()
        with col2:
            if st.button("↗ Escalate to Doctor", key=f"escalate_{case['sos_id']}"):
                run_write(
                    """
                    UPDATE sos_complaints
                    SET status = 'Escalated', nurse_reviewed_at = %s, escalated_at = %s
                    WHERE sos_id = %s
                    """,
                    (datetime.now(), datetime.now(), case["sos_id"]),
                )
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def get_sos_queue():
    return run_query(
        """
        SELECT sc.sos_id, sc.description, sc.severity, sc.status, sc.raised_at,
               p.name AS patient_name, p.age, d.name AS doctor_name
        FROM sos_complaints sc
        JOIN patients p ON sc.patient_id = p.patient_id
        LEFT JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE sc.nurse_id = %s AND sc.status IN ('Raised', 'Under Nurse Review')
        ORDER BY
            CASE sc.severity WHEN 'Urgent' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,
            sc.raised_at ASC
        """,
        (nurse_id,),
    )


def get_tasks(status_filter=None):
    sql = """
        SELECT t.task_id, t.task_type, t.status, t.notes, t.created_at, p.name AS patient_name
        FROM tasks t
        JOIN patients p ON t.patient_id = p.patient_id
        WHERE t.nurse_id = %s
    """
    params = [nurse_id]
    if status_filter and status_filter != "All":
        sql += " AND t.status = %s"
        params.append(status_filter)
    else:
        # "Overview" (status_filter=None) shows only open tasks; the "All" filter
        # on the Tasks page shows everything, completed included.
        if status_filter != "All":
            sql += " AND t.status != 'Completed'"
    sql += " ORDER BY t.created_at ASC"
    return run_query(sql, tuple(params))


def render_task_row(task):
    with st.container(border=True):
        row_l, row_r = st.columns([4, 2])
        with row_l:
            st.markdown(
                f"**{task['task_type']}** · {task['patient_name']}  \n"
                f"<span class='muted'>{task['notes'] or 'No notes yet'}</span>",
                unsafe_allow_html=True,
            )
        with row_r:
            badge_class = TASK_BADGE.get(task["status"], "badge-neutral")
            st.markdown(f"<span class='badge {badge_class}'>{task['status']}</span>", unsafe_allow_html=True)
            if task["status"] == "Pending":
                if st.button("Start", key=f"start_{task['task_id']}"):
                    run_write("UPDATE tasks SET status = 'In Progress' WHERE task_id = %s", (task["task_id"],))
                    st.rerun()
            elif task["status"] == "In Progress":
                if st.button("Mark complete", key=f"complete_{task['task_id']}"):
                    run_write(
                        "UPDATE tasks SET status = 'Completed', completed_at = %s WHERE task_id = %s",
                        (datetime.now(), task["task_id"]),
                    )
                    st.rerun()


def render_patient_list(limit=None):
    rows = patients[:limit] if limit else patients
    for p in rows:
        stats = compute_adherence(p["patient_id"], days=7)
        flag_class = "badge-amber" if stats["total"] and stats["percent"] < 70 else "badge-green"
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--border, transparent)">
                <div><b>{p['name']}</b><br><span class='muted'>{p['age']} · {with_title(p.get('doctor_name',''), 'Dr.')}</span></div>
                <span class='badge {flag_class}'>{stats['percent']}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# OVERVIEW — combined dashboard view
# ---------------------------------------------------------------------------
if section == "Overview":
    main_col, side_col = st.columns([2, 1], gap="medium")

    with main_col:
        st.markdown("<span class='eyebrow'>INCOMING</span>", unsafe_allow_html=True)
        st.markdown("#### SOS & complaints")
        st.caption("Sorted by severity, then time raised")
        cases = get_sos_queue()
        if not cases:
            st.info("No open cases right now.")
        for case in cases:
            render_sos_card(case)

        st.write("")
        st.markdown("<span class='eyebrow'>ASSIGNED BY DOCTORS</span>", unsafe_allow_html=True)
        st.markdown("#### Tasks")
        tasks = get_tasks()
        if not tasks:
            st.info("No pending tasks.")
        for task in tasks:
            render_task_row(task)

    with side_col:
        st.markdown("<span class='eyebrow'>CASE LOAD</span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### My patients")
            st.caption("7-day adherence")
            if not patients:
                st.info("No patients assigned yet.")
            render_patient_list()

# ---------------------------------------------------------------------------
# SOS QUEUE
# ---------------------------------------------------------------------------
elif section == "SOS queue":
    st.markdown("#### Incoming SOS & complaints")
    st.caption("Sorted by severity, then time raised")
    cases = get_sos_queue()
    if not cases:
        st.info("No open cases right now.")
    for case in cases:
        render_sos_card(case)

# ---------------------------------------------------------------------------
# TASKS
# ---------------------------------------------------------------------------
elif section == "Tasks":
    st.markdown("#### Tasks assigned by doctors")
    status_filter = st.radio(
        "Filter", ["All", "Pending", "In Progress", "Completed"],
        horizontal=True, label_visibility="collapsed",
    )
    tasks = get_tasks(status_filter)
    if not tasks:
        st.info("No tasks in this view.")
    for task in tasks:
        render_task_row(task)

# ---------------------------------------------------------------------------
# MY PATIENTS
# ---------------------------------------------------------------------------
elif section == "My patients":
    st.markdown("#### Assigned patients")
    if not patients:
        st.info("No patients assigned yet.")
    for p in patients:
        stats = compute_adherence(p["patient_id"], days=7)
        flag_class = "badge-amber" if stats["total"] and stats["percent"] < 70 else "badge-green"
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{p['name']}** — age {p['age']}, {p['gender']}")
                st.caption(f"Doctor: {with_title(p.get('doctor_name', ''), 'Dr.')}")
            with c2:
                st.markdown(
                    f"<div style='text-align:right'><span class='badge {flag_class}'>{stats['percent']}%</span></div>",
                    unsafe_allow_html=True,
                )
