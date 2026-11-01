"""The hub: four cards."""
from __future__ import annotations

import streamlit as st

from tag import ui

CSS = """
<style>
.hero {position:relative; border-radius:18px; overflow:hidden; min-height:230px; display:flex; align-items:flex-end;
       background:#081a2e url(%(bg)s) center/cover; box-shadow:0 10px 30px rgba(12,35,64,.18);}
.hero::before {content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,26,46,.15) 0%%, rgba(8,26,46,.82) 100%%);}
.hero .in {position:relative; padding:1.6rem 2rem 1.5rem; color:#fff; display:flex; align-items:flex-end; gap:1.4rem; width:100%%;}
.hero .in img {height:96px; filter:drop-shadow(0 2px 6px rgba(0,0,0,.4)); margin-bottom:.2rem;}
.hero h1 {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:3.3rem; line-height:.95; margin:0; letter-spacing:.01em;}
.hero h1 small {display:block; font-family:Barlow,sans-serif; font-weight:400; font-size:1.05rem; opacity:.85; letter-spacing:.08em;
                text-transform:uppercase; margin-bottom:.45rem;}
.hero p {margin:.5rem 0 0; opacity:.9; font-size:1.05rem; max-width:50rem;}
.hero .band {position:absolute; right:1.2rem; top:1.2rem; height:46px; border-radius:8px; opacity:.9;}

.cards {display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:1.1rem; margin-top:1.1rem;}
.cd {display:flex; flex-direction:column; background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden;
     box-shadow:0 2px 12px rgba(12,35,64,.06); color:var(--ink) !important; transition:transform .15s, box-shadow .15s; min-height:100%%;}
.cd:hover {transform:translateY(-3px); box-shadow:0 12px 28px rgba(12,35,64,.16);}
.cd .im {height:160px; background-size:cover; background-position:center; position:relative;}
.cd .im::after {content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,26,46,0) 50%%, rgba(8,26,46,.45) 100%%);}
.cd .tag {position:absolute; left:.8rem; top:.8rem; z-index:1; background:rgba(255,255,255,.92); color:var(--navy); font-size:.72rem;
          font-weight:700; letter-spacing:.08em; text-transform:uppercase; padding:.22rem .55rem; border-radius:999px;}
.cd .bd {padding:.9rem 1rem 1rem; display:flex; flex-direction:column; gap:.35rem; flex:1;}
.cd h3 {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:1.5rem; margin:0; color:var(--navy); line-height:1.05;}
.cd p {margin:0; color:var(--muted); font-size:.93rem; line-height:1.4; flex:1;}
.cd .go {margin-top:.5rem; color:var(--blue); font-weight:600; font-size:.92rem;}
.cd .go::after {content:" \\2192";}
.foot {margin-top:1.2rem; color:var(--muted); font-size:.85rem; display:flex; justify-content:space-between; flex-wrap:wrap; gap:.5rem;}
@media (max-width:1000px){ .cards {grid-template-columns:repeat(2, minmax(0, 1fr));} }
@media (max-width:640px){ .cards {grid-template-columns:1fr;} .hero h1 {font-size:2.3rem;} .hero .band {display:none;} }
</style>
"""

CARDS = [
    ("Tool", "Timer", "Big digits for the projector. Presets, reminders at 10, 5 and 1 minute, and a chime when time is up.",
     "/timer", "reading_room.jpg"),
    ("Mind and Brain", "Two-Point Threshold", "Pairs send their thumb and forearm readings from their phones. "
     "The class dot plots, means and 95% intervals build up live.", "/two-point", "neuron.jpg"),
    ("Physics and Peace", "Ballooniverse", "Each pair adds its three dots to the class graph of velocity against distance. "
     "Hubble's law appears on the screen as the room fills in.", "/ballooniverse", "balloon.png"),
    ("Physics and Peace", "Nuclear Diplomacy", "Five countries, five rounds. Enter the decision slips, run the attack draw, "
     "handle sanctions, then debrief.", "/diplomacy", "castle_bravo.jpg"),
]


def render():
    ui.base()
    st.html(CSS % {"bg": ui.img_uri("campus.jpg")})
    c1, c2 = st.columns([5, 1], vertical_alignment="center")
    with c1:
        ui.topbar(home=False)
    with c2:
        ui.music("lobby.mp3")
    st.html(f'<div class="hero"><img class="band" src="{ui.img_uri("fos_banner_wide.jpg")}" alt="">'
            f'<div class="in"><img src="{ui.img_uri("crown.png")}" alt="">'
            f'<div><h1><small>Frontiers of Science · Columbia University</small>Tools and Games</h1>'
            f'<p>Everything the seminar runs on one screen: a timer for the room, live class data that pairs send in from '
            f'their phones, and the diplomacy simulation.</p></div></div></div>')
    cards = "".join(
        f'<a class="cd" href="{href}" target="_top"><div class="im" style="background-image:url({ui.img_uri(img)})"><span class="tag">{tag}</span></div>'
        f'<div class="bd"><h3>{name}</h3><p>{blurb}</p><span class="go">Open</span></div></a>'
        for tag, name, blurb, href, img in CARDS)
    st.html(f'<div class="cards">{cards}</div>')
    st.html('<div class="foot"><span>Rooms and their data are kept for 24 hours, then cleared. Export to Excel any time.</span>'
            '<span>Nuclear Diplomacy: the K=1 Project, Columbia University.</span></div>')
