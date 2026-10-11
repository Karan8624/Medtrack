"""
Thin wrapper so Streamlit's multipage app (see Home.py) can show the
patient interface as a page in the same run, with no duplicated logic —
this just executes patient/app.py itself.
"""
import os
import runpy

_target = os.path.join(os.path.dirname(__file__), "..", "patient", "app.py")
runpy.run_path(_target, run_name="__main__")
