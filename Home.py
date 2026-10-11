"""
MedTrack — single entry point.

Run with:  streamlit run Home.py
(run it from the medtrack/ folder)

This is a role picker, not a login itself — each role still logs in on
its own page (that's where the real auth happens). What this gives the
team is ONE command, ONE browser tab, and ONE port for the whole demo,
with a sidebar page-switcher (Streamlit's built-in multipage feature)
instead of juggling three separate `streamlit run` processes.

The actual patient/nurse/doctor logic still lives in patient/app.py,
nurse/app.py and doctor/app.py — those files are unchanged and can still
be run standalone if someone on the team prefers that while developing.
pages/1_Patient.py etc. just execute those same files, so there is only
one copy of the real logic to maintain.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import streamlit as st
from shared.theme import inject_theme, theme_toggle

st.set_page_config(page_title="MedTrack", layout="wide", page_icon="🔗")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"
inject_theme(st.session_state.theme)

with st.sidebar:
    st.markdown("### 🔗 MedTrack")
    st.markdown("---")
    theme_toggle()

st.markdown("## 🔗 MedTrack")
st.caption("Medication, hydration and prescription adherence tracker")
st.write("")
st.markdown("#### Choose your role to continue")
st.caption("You'll log in with your own account on the next page.")
st.write("")

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("#### 🧑 Patient")
        st.caption("Track doses, hydration and symptoms, and raise an SOS.")
        st.page_link("pages/1_Patient.py", label="Continue as Patient")
with c2:
    with st.container(border=True):
        st.markdown("#### 🩹 Nurse")
        st.caption("Triage incoming SOS cases and manage assigned tasks.")
        st.page_link("pages/2_Nurse.py", label="Continue as Nurse")
with c3:
    with st.container(border=True):
        st.markdown("#### 🩺 Doctor")
        st.caption("Prescribe medication and review escalated cases.")
        st.page_link("pages/3_Doctor.py", label="Continue as Doctor")
