"""The timer: Erfan's full-screen countdown page, shown inside the app.

The page itself is static/timer.html. It runs in an iframe that fills the window, so
its keyboard shortcuts, dark and light screens and saved text all work as before.
"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from tag import ui

HTML = Path(__file__).resolve().parent.parent / "static" / "timer.html"

CSS = """
<style>
.block-container {padding:0 !important; max-width:100% !important;}
header[data-testid="stHeader"] {display:none;}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:0;}
iframe[title="st.iframe"], [data-testid="stIFrame"] iframe {height:100vh !important; min-height:600px; width:100% !important; display:block;}
</style>
"""


@st.cache_data(show_spinner=False)
def page_html() -> str:
    html = HTML.read_text(encoding="utf-8")
    music = ui.SOUNDS / "lobby.mp3"
    uri = "data:audio/mpeg;base64," + base64.b64encode(music.read_bytes()).decode()
    html = html.replace("new Audio('sounds/lobby.mp3')", f"new Audio('{uri}')")
    html = html.replace('<a class="homelink" href="/"',
                        '<a class="homelink" href="/" onclick="window.parent.postMessage(\'fos-home\', \'*\'); return false;"')
    html = html.replace("track.loop = true;", "window.__fosTrack = track; track.loop = true;", 1)
    return html


def render():
    ui.base()
    st.html(CSS)
    components.html(page_html(), height=1000, scrolling=False)
