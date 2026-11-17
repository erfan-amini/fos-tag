"""FroSci Seminar Kit: tools for Frontiers of Science seminars.

One app, five things: a timer for the room, two live class-data activities that pairs
feed from their phones (Two-Point Threshold, Ballooniverse), the Nuclear Diplomacy
simulation, and a live Debate with a voting panel. Run locally with:  streamlit run streamlit_app.py
"""
from pathlib import Path

import streamlit as st

from tag import balloon, debate, diplomacy, home, timer, tpt

st.set_page_config(page_title="FroSci Seminar Kit", page_icon=str(Path(__file__).parent / "assets" / "img" / "crown.png"),
                   layout="wide", initial_sidebar_state="expanded")

pages = [
    st.Page(home.render, title="FroSci Seminar Kit", url_path="", default=True),
    st.Page(timer.render, title="Timer", url_path="timer"),
    st.Page(tpt.render, title="Two-Point Threshold", url_path="two-point"),
    st.Page(balloon.render, title="Ballooniverse", url_path="ballooniverse"),
    st.Page(diplomacy.render, title="Nuclear Diplomacy", url_path="diplomacy"),
    st.Page(debate.render, title="Debate", url_path="debate"),
]
st.navigation(pages, position="hidden").run()
