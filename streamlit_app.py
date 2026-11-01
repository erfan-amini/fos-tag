"""FoS TaG: Frontiers of Science tools and games.

One app, four things: a timer for the room, two live class-data activities that pairs
feed from their phones (Two-Point Threshold, Ballooniverse), and the Nuclear Diplomacy
simulation. Run locally with:  streamlit run streamlit_app.py
"""
from pathlib import Path

import streamlit as st

from tag import balloon, diplomacy, home, tpt

st.set_page_config(page_title="FoS TaG", page_icon=str(Path(__file__).parent / "assets" / "img" / "crown.png"),
                   layout="wide", initial_sidebar_state="expanded")

pages = [
    st.Page(home.render, title="FoS TaG", url_path="", default=True),
    st.Page(tpt.render, title="Two-Point Threshold", url_path="two-point"),
    st.Page(balloon.render, title="Ballooniverse", url_path="ballooniverse"),
    st.Page(diplomacy.render, title="Nuclear Diplomacy", url_path="diplomacy"),
]
st.navigation(pages, position="hidden").run()
