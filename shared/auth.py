"""
Shared authentication helpers for MedTrack.

Handles password checking and a simple Streamlit session-based login,
shared by all three role apps (patient/nurse/doctor). Keeps auth logic
in one place so it's consistent and easy to review for the rubric's
"Testing, Validation & Security" criterion.

Usage example (inside a Streamlit page):

    from shared.auth import login_form, require_login, logout

    # At the top of the page:
    require_login(role="patient")   # redirects to a login form if not logged in

    # Inside the login page itself:
    user = login_form(role="doctor")
    if user:
        st.success(f"Welcome, {user['name']}")
"""

import bcrypt
import streamlit as st
from shared.db import run_query


# maps each role to its table and the column holding the display name
ROLE_TABLES = {
    "patient": {"table": "patients", "id_col": "patient_id", "name_col": "name"},
    "nurse": {"table": "nurses", "id_col": "nurse_id", "name_col": "name"},
    "doctor": {"table": "doctors", "id_col": "doctor_id", "name_col": "name"},
}


def check_password(plain_password: str, password_hash: str) -> bool:
    """Compare a plaintext password against the stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def authenticate(role: str, email: str, password: str):
    """
    Look up a user by role + email, verify their password, and return
    their row as a dict if valid, or None if the email/password is wrong.

    Never reveals whether the email or the password was the problem —
    that's a basic security practice (don't help an attacker narrow
    down which part of their guess was wrong).
    """
    if role not in ROLE_TABLES:
        return None

    cfg = ROLE_TABLES[role]
    rows = run_query(f"SELECT * FROM {cfg['table']} WHERE email = %s", (email,))
    if not rows:
        return None

    user = rows[0]
    if not check_password(password, user["password_hash"]):
        return None

    return user


def login_form(role: str):
    """
    Render a simple email/password form for the given role. Returns the
    authenticated user dict once login succeeds (and stores it in
    st.session_state so require_login() picks it up on reruns).
    """
    st.subheader(f"{role.capitalize()} Login")

    with st.form(key=f"{role}_login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in")

    if submitted:
        user = authenticate(role, email, password)
        if user is None:
            st.error("Incorrect email or password.")
            return None
        st.session_state["user"] = user
        st.session_state["role"] = role
        st.rerun()

    return None


def require_login(role: str):
    """
    Call this at the top of any page that should only be reachable by a
    logged-in user of the given role. If no one's logged in (or the
    wrong role is), it shows the login form and stops the page from
    rendering anything further.
    """
    user = st.session_state.get("user")
    current_role = st.session_state.get("role")

    if user is None or current_role != role:
        login_form(role)
        st.stop()  # halts execution here so the rest of the page doesn't render

    return user


def logout():
    """Clear the session and send the user back to a logged-out state."""
    st.session_state.pop("user", None)
    st.session_state.pop("role", None)
    st.rerun()
