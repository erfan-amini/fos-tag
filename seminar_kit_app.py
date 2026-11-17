"""The same app again, for the second address: frosci-seminar-kit.streamlit.app.

Streamlit Community Cloud gives each deployed app one address and deploys a given file only once,
so this file just runs streamlit_app.py. Each address keeps its own rooms; the QR code and join link
on a board always carry that board's own address, so students land in the right place.
"""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name("streamlit_app.py")), run_name="__main__")
