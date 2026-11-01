"""Shared look and small building blocks: the top bar, cards, images and sounds."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
SOUNDS = ROOT / "static" / "sounds"

NAVY = "#0C2340"
BLUE = "#1F5AA6"
SKY = "#B9D9EB"
INK = "#18202C"
MUTED = "#5E6878"
LINE = "#DCE1E8"
PANEL = "#F3F5F8"


@st.cache_data(show_spinner=False)
def img_uri(name: str) -> str:
    p = IMG / name
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
            "svg": "image/svg+xml"}[p.suffix.lstrip(".").lower()]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


@st.cache_data(show_spinner=False)
def sound_bytes(name: str) -> bytes:
    return (SOUNDS / name).read_bytes()


BASE_CSS = """
<style>
:root {
  --navy:#0C2340; --blue:#1F5AA6; --sky:#B9D9EB; --ink:#18202C; --muted:#5E6878; --line:#DCE1E8; --panel:#F3F5F8;
  --signal:#C00000; --amber:#F2B705; --calm:#1E7B6B;
}
header[data-testid="stHeader"] {background:transparent; height:2.2rem;}
/* On Streamlit Cloud the header grows to ~64px (Share, star, GitHub) and silently swallows clicks on anything
   under it: our Home button and the Music switch. Let clicks pass through it, except on its own buttons. */
header[data-testid="stHeader"], header[data-testid="stHeader"] * {pointer-events:none;}
header[data-testid="stHeader"] button, header[data-testid="stHeader"] a, header[data-testid="stHeader"] [role="button"],
header[data-testid="stHeader"] [role="menu"], header[data-testid="stHeader"] [role="menu"] * {pointer-events:auto;}
.block-container {padding-top:.8rem !important; padding-bottom:1.2rem !important; max-width:1360px;}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {gap:.65rem;}
[data-testid="stAudio"] {display:none;}
a {text-decoration:none;}

/* top bar */
.tb {display:flex; align-items:center; gap:1rem; min-height:3rem; padding-right:11rem;}
.tb .home {display:inline-flex; align-items:center; gap:.4rem; padding:.42rem .9rem .42rem .7rem; border-radius:999px;
           background:var(--navy); color:#fff !important; font-weight:600; font-size:.95rem; letter-spacing:.01em;
           box-shadow:0 2px 8px rgba(12,35,64,.18); transition:transform .12s, box-shadow .12s;}
.tb .home:hover {transform:translateY(-1px); box-shadow:0 4px 14px rgba(12,35,64,.25);}
.tb .home svg {width:17px; height:17px;}
.tb .crown {height:30px;}
.tb .wm {display:flex; flex-direction:column; line-height:1.05;}
.tb .wm b {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:1.55rem; color:var(--navy); letter-spacing:.01em;}
.tb .wm span {color:var(--muted); font-size:.78rem; letter-spacing:.06em; text-transform:uppercase; white-space:nowrap;}
.tb .ttl {margin-left:.4rem; padding-left:1.2rem; border-left:2px solid var(--line); font-family:"Barlow Condensed",sans-serif;
          font-weight:700; font-size:1.7rem; color:var(--ink); line-height:1; white-space:nowrap;}
.tb .ttl small {display:block; font-family:Barlow,sans-serif; font-weight:400; font-size:.86rem; color:var(--muted); margin-top:.2rem;}

/* music switch sits in a small right column */
[class*="st-key-music"] [data-testid="stToggle"] {justify-content:flex-end;}
[class*="st-key-music"] label p {font-size:.85rem; color:var(--muted);}

/* generic pieces */
.card {background:#fff; border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem; box-shadow:0 2px 10px rgba(12,35,64,.05);}
.lede {color:var(--muted); font-size:1.02rem; max-width:62rem; margin:0;}
h2.vt {font-family:"Barlow Condensed",sans-serif; font-size:1.35rem; font-weight:700; color:var(--navy); margin:.2rem 0 .3rem; letter-spacing:.01em;}
.kpi {display:flex; gap:.8rem; flex-wrap:wrap;}
.kpi .k {background:var(--panel); border-radius:12px; padding:.55rem .9rem; min-width:7.5rem;}
.kpi .k b {display:block; font-family:"Barlow Condensed",sans-serif; font-size:1.55rem; line-height:1.05; color:var(--ink);}
.kpi .k span {font-size:.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em;}
.pill {display:inline-block; padding:.2rem .6rem; border-radius:999px; font-size:.8rem; font-weight:600; background:var(--panel); color:var(--muted);}
.pill.ok {background:#E3F5EA; color:#1E7B46;} .pill.wait {background:#FFF4D6; color:#8A5A00;}
.small {color:var(--muted); font-size:.88rem;}
.err {color:var(--signal); font-weight:600;}

/* keep columns side by side on phones where we ask for it */
[class*="st-key-grid"] [data-testid="stHorizontalBlock"] {flex-wrap:wrap; gap:.4rem;}
[class*="st-key-grid"] [data-testid="stColumn"] {min-width:0 !important; flex:1 1 0 !important; width:auto !important;}

/* symbol tiles: the whole tile is the button (an invisible button is stretched over the symbol and its name) */
[class*="st-key-tile_"] {position:relative; border:2px solid var(--line); border-radius:12px; padding:.4rem .2rem .35rem; text-align:center;
                         background:#fff; cursor:pointer;}
[class*="st-key-tile_"] [data-testid="stHtml"] {display:flex; justify-content:center;}
[class*="st-key-tile_"] .tile-in {display:flex; flex-direction:column; align-items:center; gap:.2rem;}
[class*="st-key-tile_"] .tile-name {font-size:.74rem; color:var(--muted); white-space:nowrap; line-height:1.1;}
[class*="st-key-tile_"] [data-testid="stElementContainer"]:last-child {position:absolute; inset:0; margin:0; z-index:2;}
[class*="st-key-tile_"] [data-testid="stButton"] {height:100%;}
[class*="st-key-tile_"] button {width:100%; height:100%; min-height:0; margin:0; padding:0; border:0; background:transparent; opacity:0;}
[class*="st-key-tile_"]:hover {border-color:var(--blue);}
[class*="st-key-tile_"][class*="_on"] {border-color:var(--navy); background:#EEF4FB; box-shadow:0 0 0 3px rgba(31,90,166,.15);}
[class*="st-key-tile_"][class*="_on"] .tile-name {color:var(--navy); font-weight:600;}
[class*="st-key-tile_"][class*="_taken"] {opacity:.35; cursor:not-allowed;}
[class*="st-key-sw_"] button {min-height:2.2rem; width:100%; border-radius:10px; border:3px solid transparent; padding:0;}
[class*="st-key-sw_"][class*="_on"] button {border-color:var(--ink); box-shadow:0 0 0 2px #fff inset;}

/* board (projector) type */
.board-code {display:flex; align-items:center; gap:1.4rem;}
.board-code .code {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:4.4rem; letter-spacing:.14em; line-height:1; color:var(--navy);}
.board-code .how {color:var(--muted); font-size:1rem; line-height:1.35; margin-top:.3rem;}
.board-code .how b {color:var(--ink);}
.board-code .url {font-family:"Barlow Condensed",sans-serif; font-size:1.35rem; color:var(--blue); font-weight:600;}
.joined {display:flex; flex-wrap:wrap; gap:.45rem .7rem; align-items:center;}
.joined .pr {display:inline-flex; align-items:center; gap:.35rem; padding:.25rem .65rem .25rem .4rem; border-radius:999px;
             border:1px solid var(--line); background:#fff; font-size:.92rem;}
.joined .pr.wait {opacity:.55; border-style:dashed;}
.stat-row {display:flex; gap:.6rem; flex-wrap:wrap; align-items:stretch;}
.stat {flex:1 1 9rem; background:#fff; border:1px solid var(--line); border-radius:12px; padding:.5rem .8rem;}
.stat .t {font-size:.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:.06em;}
.stat .v {font-family:"Barlow Condensed",sans-serif; font-size:1.7rem; font-weight:700; color:var(--ink); line-height:1.1;}
.stat .s {font-size:.85rem; color:var(--muted);}
.verdict {border-radius:12px; padding:.7rem 1rem; font-size:1.05rem; background:var(--panel);}
.verdict b {color:var(--navy);}
.verdict.yes {background:#E3F5EA;} .verdict.no {background:#FDE8E6;}

/* phone entry */
.saved {background:#E3F5EA; border-radius:12px; padding:.8rem 1rem; color:#1E7B46; font-weight:600;}
.p-head {display:flex; align-items:center; gap:.6rem; font-family:"Barlow Condensed",sans-serif; font-size:1.3rem; font-weight:700; color:var(--navy); margin-top:.3rem;}
.mean-line {background:var(--panel); border-radius:10px; padding:.45rem .8rem; font-size:.95rem; color:var(--ink);}
.mean-line b {font-family:"Barlow Condensed",sans-serif; font-size:1.25rem;}
@media (max-width:640px){
  .block-container {padding-left:.8rem !important; padding-right:.8rem !important;}
  .tb {padding-right:0; flex-wrap:wrap; gap:.5rem .7rem; min-height:0;}
  .tb .wm span {display:none;} .tb .wm b {font-size:1.3rem;} .tb .crown {height:24px;}
  .tb .ttl {border-left:0; padding-left:0; margin-left:0; font-size:1.35rem; flex-basis:100%; white-space:normal;}
  .tb .ttl small {display:inline; margin-left:.4rem;}
}
</style>
"""

_HOME = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" '
         'stroke-linecap="round" stroke-linejoin="round"><path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/></svg>')
HOME_SVG = ('<img src="data:image/svg+xml;base64,' + base64.b64encode(_HOME.encode()).decode()
            + '" width="17" height="17" alt="" style="display:inline-block">')


# Streamlit Community Cloud shows the app inside an iframe, and st.html drops target attributes,
# so internal links are sent to the top window by hand. The timer's own Home link asks for it by message.
TOP_NAV_JS = """
<script>
(function () {
  if (window.__fosNav) { return; }
  window.__fosNav = true;
  // Move to another page of this app through Streamlit's own router (works inside the
  // Streamlit Community Cloud iframe, where the top window cannot be navigated).
  function goPage(path) {
    var q = path.indexOf('?');
    var page = (q >= 0 ? path.slice(0, q) : path).replace(/^\/+/, '');
    var search = q >= 0 ? path.slice(q) : '';
    var base = window.location.pathname.replace(/[^/]*$/, '');
    history.pushState({}, '', base + page + search);
    window.dispatchEvent(new PopStateEvent('popstate', { state: {} }));
  }
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) { return; }
    var href = a.getAttribute('href') || '';
    if (href.charAt(0) !== '/' || href.indexOf('//') === 0) { return; }
    e.preventDefault();
    goPage(href);
  }, true);
  window.addEventListener('message', function (e) {
    if (e.data === 'fos-home') { goPage('/'); }
  });
})();
</script>
"""


def base():
    st.html(BASE_CSS)
    st.html(TOP_NAV_JS, unsafe_allow_javascript=True)


def topbar_html(title: str = "", subtitle: str = "", home: bool = True) -> str:
    home_html = f'<a class="home" href="/" target="_top">{HOME_SVG}Home</a>' if home else ""
    ttl = f'<div class="ttl">{title}<small>{subtitle}</small></div>' if title else ""
    return (f'{home_html}<img class="crown" src="{img_uri("crown.png")}" alt="">'
            f'<div class="wm"><b>FoS TaG</b><span>Frontiers of Science · Tools and Games</span></div>{ttl}')


def topbar(title: str = "", subtitle: str = "", home: bool = True):
    """Home pill, crown and wordmark, then the page title."""
    st.html(f'<div class="tb">{topbar_html(title, subtitle, home)}</div>')


def music(track: str, default: bool = False, label: str = "Music"):
    """A looping background track with a switch. Hidden audio element, so only the switch shows."""
    key = f"music_{track}"
    on = st.session_state.setdefault("music_on", default)
    with st.container(key="music_switch"):
        on = st.toggle(label, value=on, key=f"music_t_{track}", help="Background music for the room")
    st.session_state["music_on"] = on
    if on:
        with st.container(key=key):
            st.audio(sound_bytes(track), format="audio/mp3", loop=True, autoplay=True)


def play(slot, track: str):
    """Play a one-shot sound in a given st.empty() slot."""
    slot.audio(sound_bytes(track), format="audio/mp3", autoplay=True)


def kpi(items: list[tuple[str, str]]) -> str:
    return '<div class="kpi">' + "".join(f'<div class="k"><b>{v}</b><span>{k}</span></div>' for k, v in items) + "</div>"
