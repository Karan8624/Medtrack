"""
Thin wrapper so Streamlit's multipage app (see Home.py) can show the
doctor interface as a page in the same run, with no duplicated logic —
this just executes doctor/app.py itself.
"""
import os
import runpy

_target = os.path.join(os.path.dirname(__file__), "..", "doctor", "app.py")
runpy.run_path(_target, run_name="__main__")
