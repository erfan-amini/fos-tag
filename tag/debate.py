"""Debate: teams argue a resolution, the rest of the room is the panel.

The board (projector) shows the resolution, the two sides, the clock and where the panel
stands. Each student joins from a phone, picks a team, and then either sees which side the
team argues, or, as a panel member, picks a side before the opening, reacts to each speech
with an emoji, changes sides while listening, and gives a final vote.
"""
from __future__ import annotations

import math
import time

import streamlit as st

from tag import debate_logic as L
from tag import rooms, ui
from tag.store import get_store

PATH = "debate"
KIND = "debate"
TITLE = "Debate"
NUM = ["Zero", "One", "Two", "Three", "Four", "Five", "Six"]

CSS = """
<style>
:root {--for:#1E7B46; --for-bg:#E3F5EA; --against:#B4282C; --against-bg:#FCE9E8; --und:#8A93A3; --und-bg:#EEF0F4;}

/* clock: the digits are kept moving by a small script, the server sends where the clock stands */
.dbt-clock {font-family:"Barlow Condensed",sans-serif; font-weight:700; color:var(--navy); line-height:.9; text-align:center;
            font-variant-numeric:tabular-nums; letter-spacing:.01em;}
.dbt-clock.big {font-size:8.2rem;} .dbt-clock.mid {font-size:3.4rem;}
.dbt-clock.warn {color:#C77700;} .dbt-clock.hot {color:var(--against); animation:dbt-pulse 1s ease-in-out infinite;}
.dbt-clock.over {color:var(--against); animation:dbt-pulse .7s ease-in-out infinite;}
@keyframes dbt-pulse {50% {opacity:.45;}}

/* lobby */
.dbt-hero {position:relative; border-radius:18px; overflow:hidden; min-height:300px; display:flex; align-items:flex-end;
           background-color:#081a2e; background-size:cover; background-position:center 30%; box-shadow:0 10px 30px rgba(12,35,64,.18);}
.dbt-hero::before {content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,26,46,.05) 0%, rgba(8,26,46,.88) 100%);}
.dbt-hero .in {position:relative; padding:1.4rem 1.7rem 1.3rem; color:#fff;}
.dbt-hero .k {font-size:.86rem; letter-spacing:.12em; text-transform:uppercase; opacity:.85;}
.dbt-hero h1 {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:4.4rem; line-height:.95; margin:.1rem 0 .3rem; color:#fff;}
.dbt-hero p {margin:0; font-size:1.25rem; line-height:1.3; opacity:.95;}
.dbt-hero.small {min-height:150px;} .dbt-hero.small h1 {font-size:2.6rem;} .dbt-hero.small p {font-size:1rem;}
.dbt-teams {display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:.7rem;}
.dbt-team {background:#fff; border:1px solid var(--line); border-top:6px solid var(--c); border-radius:14px; padding:.6rem .9rem .75rem; min-height:7.2rem;}
.dbt-team .n {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:1.7rem; color:var(--c); line-height:1; display:flex; justify-content:space-between; align-items:baseline;}
.dbt-team .n small {font-family:Barlow,sans-serif; font-weight:500; font-size:.85rem; color:var(--muted);}
.dbt-team .m {display:flex; flex-wrap:wrap; gap:.3rem .35rem; margin-top:.45rem;}
.dbt-team .m span {background:var(--panel); border-radius:999px; padding:.12rem .6rem; font-size:.95rem;}
.dbt-team .m i {color:var(--muted); font-size:.9rem;}
.dbt-how {display:flex; gap:.5rem; flex-wrap:wrap; align-items:stretch;}
.dbt-how div {flex:1 1 6rem; background:var(--panel); border-radius:12px; padding:.45rem .7rem; font-size:.9rem; color:var(--muted); line-height:1.25;}
.dbt-how b {display:block; font-family:"Barlow Condensed",sans-serif; font-size:1.5rem; color:var(--navy); line-height:1.05;}

/* the resolution */
.dbt-res {background:var(--navy); color:#fff; border-radius:16px; padding:.85rem 1.3rem 1rem; box-shadow:0 6px 20px rgba(12,35,64,.2);}
.dbt-res .k {font-size:.82rem; letter-spacing:.12em; text-transform:uppercase; color:var(--sky); display:flex; justify-content:space-between; gap:1rem; flex-wrap:wrap;}
.dbt-res .k .addr {text-transform:none; letter-spacing:.02em; opacity:.9;}
.dbt-res .q {font-family:"Barlow Condensed",sans-serif; font-weight:600; font-size:2.25rem; line-height:1.1; margin:.25rem 0 .1rem;}
.dbt-res .scene {opacity:.8; font-size:1rem;}
.dbt-res.phone {padding:.6rem .85rem .7rem; border-radius:14px;} .dbt-res.phone .q {font-size:1.22rem; margin-top:.15rem;}
.dbt-res.phone .k {font-size:.72rem;} .dbt-res.phone .scene {display:none;}
.dbt-track {display:flex; gap:.3rem; flex-wrap:wrap; margin-top:.6rem;}
.dbt-track span {font-size:.8rem; padding:.16rem .6rem; border-radius:999px; background:rgba(255,255,255,.1); color:rgba(255,255,255,.65); white-space:nowrap;}
.dbt-track span.done {color:rgba(255,255,255,.4); text-decoration:line-through;}
.dbt-track span.on {background:#fff; color:var(--navy); font-weight:700;}
.dbt-track span.on.for {background:#BFEBD0;} .dbt-track span.on.against {background:#F8C9C6;}

/* the two sides */
.dbt-side {position:relative; border-radius:16px; overflow:hidden; min-height:340px; color:#fff; display:flex; flex-direction:column;
           justify-content:flex-end; background-size:cover; background-position:center; border:5px solid transparent;
           box-shadow:0 4px 16px rgba(12,35,64,.14); transition:box-shadow .3s, transform .3s;}
.dbt-side.for {background-color:var(--for);} .dbt-side.against {background-color:var(--against);}
.dbt-side::before {content:""; position:absolute; inset:0;}
.dbt-side.for::before {background:linear-gradient(180deg, rgba(18,84,46,.25) 0%, rgba(13,62,34,.93) 78%);}
.dbt-side.against::before {background:linear-gradient(180deg, rgba(130,24,28,.25) 0%, rgba(96,16,20,.93) 78%);}
.dbt-side.live {border-color:#FFD43B; box-shadow:0 0 0 4px rgba(255,212,59,.35), 0 10px 30px rgba(12,35,64,.3); transform:translateY(-3px);}
.dbt-side.dim {opacity:.62;}
.dbt-side .in {position:relative; padding:.9rem 1.1rem 1rem;}
.dbt-side .tag {font-size:.85rem; letter-spacing:.16em; text-transform:uppercase; font-weight:700; opacity:.9;}
.dbt-side .tm {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:3.2rem; line-height:.95;}
.dbt-side .cap {font-size:1.05rem; opacity:.92; margin-top:.1rem;}
.dbt-side .mem {font-size:.92rem; opacity:.8; margin-top:.35rem; line-height:1.3;}
.dbt-side .rx {display:flex; flex-wrap:wrap; gap:.35rem .5rem; margin-top:.55rem; font-size:1.2rem; font-family:"Barlow Condensed",sans-serif; font-weight:600;}
.dbt-side .rx span {background:rgba(255,255,255,.14); border-radius:999px; padding:.05rem .6rem .05rem .45rem;}
.dbt-side .badge {position:absolute; top:.8rem; left:.8rem; background:#FFD43B; color:#3b2f00; font-weight:700; font-size:.85rem;
                  letter-spacing:.1em; text-transform:uppercase; padding:.25rem .7rem; border-radius:999px;}
.dbt-side .big {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:5.2rem; line-height:.9;}
.dbt-side .big small {font-size:1.3rem; font-weight:500; opacity:.85; margin-left:.4rem;}
.dbt-fl {position:absolute; bottom:38%; font-size:2.9rem; line-height:1; pointer-events:none; opacity:0;
         animation:dbt-rise 3.6s ease-out forwards; filter:drop-shadow(0 3px 6px rgba(0,0,0,.45)); z-index:3;}
@keyframes dbt-rise {0% {transform:translateY(40px) scale(.5); opacity:0;} 10% {opacity:1; transform:translateY(0) scale(1.2);}
                     75% {opacity:1;} 100% {transform:translateY(-190px) scale(1); opacity:0;}}

/* centre column */
.dbt-now {text-align:center; margin-top:.2rem;}
.dbt-now .a {font-size:.85rem; letter-spacing:.14em; text-transform:uppercase; color:var(--muted);}
.dbt-now .b {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:2.3rem; line-height:1; color:var(--ink);}
.dbt-now .b.for {color:var(--for);} .dbt-now .b.against {color:var(--against);}
.dbt-now .c {color:var(--muted); font-size:.95rem; margin-top:.25rem; min-height:1.3rem;}
[class*="st-key-dbt_ctl"] button {min-height:2.6rem; padding:.2rem .35rem;}
[class*="st-key-dbt_ctl"] button p {white-space:nowrap;}
[class*="st-key-dbt_ctl"] [data-testid="stHorizontalBlock"] {gap:.4rem;}

/* where the panel stands */
.dbt-pan {background:#fff; border:1px solid var(--line); border-radius:14px; padding:.6rem .9rem .75rem;}
.dbt-pan .h {display:flex; justify-content:space-between; align-items:baseline; gap:1rem; flex-wrap:wrap; margin-bottom:.4rem;}
.dbt-pan .h b {font-family:"Barlow Condensed",sans-serif; font-size:1.35rem; color:var(--navy);}
.dbt-pan .h span {color:var(--muted); font-size:.92rem;}
.dbt-bar {display:flex; height:3.3rem; border-radius:12px; overflow:hidden; background:var(--und-bg); gap:3px;}
.dbt-bar.thin {height:1.5rem; border-radius:8px;}
.dbt-bar div {display:flex; align-items:center; justify-content:center; color:#fff; font-family:"Barlow Condensed",sans-serif;
              font-weight:700; font-size:1.55rem; white-space:nowrap; min-width:0; overflow:hidden;}
.dbt-bar.thin div {font-size:.95rem;}
.dbt-bar .for {background:var(--for);} .dbt-bar .against {background:var(--against);} .dbt-bar .und {background:var(--und);}
.dbt-bar .lock {flex:1; color:var(--muted); font-family:Barlow,sans-serif; font-weight:500; font-size:1.05rem; background:
                repeating-linear-gradient(135deg, #EEF0F4 0 14px, #E4E7ED 14px 28px);}
.dbt-rows {display:grid; grid-template-columns:4.6rem 1fr; gap:.3rem .6rem; align-items:center; font-size:.9rem; color:var(--muted);}

/* result */
.dbt-win {border-radius:16px; padding:1rem 1rem 1.1rem; text-align:center; color:#fff; background-color:var(--navy);
          background-size:cover; background-position:center; position:relative; overflow:hidden; min-height:230px;
          display:flex; flex-direction:column; justify-content:flex-end;}
.dbt-win::before {content:""; position:absolute; inset:0; background:linear-gradient(180deg, rgba(8,26,46,.25) 0%, rgba(8,26,46,.92) 80%);}
.dbt-win > * {position:relative;}
.dbt-win .k {font-size:.82rem; letter-spacing:.14em; text-transform:uppercase; opacity:.85;}
.dbt-win .w {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:2.5rem; line-height:1; margin:.15rem 0;}
.dbt-win .s {font-size:1rem; opacity:.9;}
.dbt-sum {display:grid; grid-template-columns:repeat(auto-fit, minmax(20rem, 1fr)); gap:.8rem;}
.dbt-deb {background:#fff; border:1px solid var(--line); border-radius:14px; padding:.9rem 1.2rem;}
.dbt-deb ol {margin:.3rem 0 0; padding-left:1.4rem; font-size:1.35rem; line-height:1.35; color:var(--ink);}
.dbt-deb li {margin:.25rem 0;}

/* phone */
.dbt-me {display:flex; align-items:center; gap:.5rem; font-family:"Barlow Condensed",sans-serif; font-size:1.35rem; font-weight:700; color:var(--navy);}
.dbt-me span {background:var(--c); color:#fff; border-radius:999px; padding:.05rem .7rem; font-size:1.05rem;}
.dbt-role {border-radius:16px; padding:1rem 1.1rem; color:#fff; text-align:center;}
.dbt-role.for {background:var(--for);} .dbt-role.against {background:var(--against);} .dbt-role.panel {background:var(--navy);}
.dbt-role .a {font-size:.82rem; letter-spacing:.14em; text-transform:uppercase; opacity:.9;}
.dbt-role .b {font-family:"Barlow Condensed",sans-serif; font-weight:700; font-size:2.6rem; line-height:1;}
.dbt-role .c {font-size:.98rem; opacity:.95; margin-top:.25rem;}
.dbt-turn {border-radius:12px; padding:.6rem .9rem; font-weight:600; text-align:center; background:var(--panel); color:var(--ink);}
.dbt-turn.you {background:#FFF1B8; color:#5c4500; animation:dbt-pulse 1.4s ease-in-out infinite;}
.dbt-line {display:flex; align-items:center; justify-content:space-between; gap:.8rem; background:var(--panel); border-radius:12px; padding:.4rem .9rem;}
.dbt-line .l small {display:block; font-size:.74rem; letter-spacing:.1em; text-transform:uppercase; color:var(--muted);}
.dbt-line .l b {font-family:"Barlow Condensed",sans-serif; font-size:1.4rem; line-height:1.05;}
.dbt-line .l b.for {color:var(--for);} .dbt-line .l b.against {color:var(--against);}
.dbt-cap {font-size:.8rem; color:var(--muted); text-align:center; line-height:1.1; margin-top:-.35rem;}
.dbt-sent {text-align:center; color:var(--muted); font-size:.9rem; min-height:1.2rem;}
[class*="st-key-dbt_s_"] button {min-height:4rem; border-width:2px; border-style:solid; font-weight:700; background:#fff;}
[class*="st-key-dbt_s_"] button p {font-size:1.12rem; font-weight:700;}
[class*="st-key-dbt_s_for_"] button {border-color:var(--for); color:var(--for);}
[class*="st-key-dbt_s_against_"] button {border-color:var(--against); color:var(--against);}
[class*="st-key-dbt_s_und_"] button {border-color:var(--und); color:#5E6878;}
[class*="st-key-dbt_s_for_on"] button, [class*="st-key-dbt_s_for_on"] button:is(:hover, :focus, :active) {background:var(--for) !important; border-color:var(--for) !important; box-shadow:0 0 0 3px rgba(30,123,70,.25);}
[class*="st-key-dbt_s_against_on"] button, [class*="st-key-dbt_s_against_on"] button:is(:hover, :focus, :active) {background:var(--against) !important; border-color:var(--against) !important; box-shadow:0 0 0 3px rgba(180,40,44,.25);}
[class*="st-key-dbt_s_und_on"] button, [class*="st-key-dbt_s_und_on"] button:is(:hover, :focus, :active) {background:var(--und) !important; border-color:var(--und) !important; box-shadow:0 0 0 3px rgba(138,147,163,.3);}
[class*="st-key-dbt_s_"][class*="_on"] button p {color:#fff !important;}
[class*="st-key-dbt_s_"][class*="_off"] button:is(:hover, :focus, :active) {background:#fff !important;}
[class*="st-key-dbt_s_for_off"] button p {color:var(--for) !important;} [class*="st-key-dbt_s_against_off"] button p {color:var(--against) !important;}
[class*="st-key-dbt_s_und_off"] button p {color:#5E6878 !important;}
[class*="st-key-dbt_rx_"] button {min-height:3.6rem; background:#fff; border:2px solid var(--line); border-radius:14px;}
[class*="st-key-dbt_rx_"] button p {font-size:2.1rem; line-height:1;}
[class*="st-key-dbt_rx_"] button:active {transform:scale(.92); background:#FFF6D6;}
[class*="st-key-dbt_t_"] button {min-height:3.6rem; border:2px solid var(--line); background:#fff; font-weight:700;}
[class*="st-key-dbt_t_"] button p {font-size:1.1rem; font-weight:700;}
[class*="st-key-dbt_t_"][class*="_on"] button {border-color:var(--navy); background:#EEF4FB; box-shadow:0 0 0 3px rgba(31,90,166,.18);}
.dbt-credit {color:var(--muted); font-size:.78rem; line-height:1.35; margin-top:.4rem;}
@media (max-width:640px){ .dbt-teams {grid-template-columns:1fr 1fr;} .dbt-team .n {font-size:1.3rem;} .dbt-deb ol {font-size:1.08rem;} }
</style>
"""

# One ticker for every clock on the page. A clock element carries the seconds left when the server drew it,
# whether it runs, and a key that changes on every start, pause or reset. The ticker fixes the end time the
# first time it sees a key, so later redraws (once a second or two) do not make the digits jump.
CLOCK_JS = r"""
<script>
(function () {
  if (window.__dbtClock) { return; }
  window.__dbtClock = true;
  var ends = {};
  function fmt(s) { s = Math.max(0, Math.ceil(s)); var m = Math.floor(s / 60), x = s % 60; return m + ':' + (x < 10 ? '0' : '') + x; }
  setInterval(function () {
    var els = document.querySelectorAll('.dbt-clock');
    for (var i = 0; i < els.length; i++) {
      var el = els[i], left = parseFloat(el.getAttribute('data-left')) || 0, k = el.getAttribute('data-k');
      var rem = left;
      if (el.getAttribute('data-run') === '1') {
        if (!(k in ends)) { ends[k] = performance.now() + left * 1000; }
        rem = (ends[k] - performance.now()) / 1000;
      }
      var txt = rem <= 0 ? 'Time!' : fmt(rem), t = el.querySelector('.t');
      if (t && t.textContent !== txt) { t.textContent = txt; }
      el.classList.toggle('warn', rem <= 30 && rem > 10);
      el.classList.toggle('hot', rem <= 10 && rem > 0);
      el.classList.toggle('over', rem <= 0);
    }
  }, 200);
})();
</script>
"""


# ---------------------------------------------------------------------------- small pieces
def _base():
    ui.base()
    st.html(CSS)
    st.html(CLOCK_JS, unsafe_allow_javascript=True)


def _img(name: str) -> str:
    try:
        return ui.img_uri(name) if name else ""
    except Exception:
        return ""


def _image_css(room: dict) -> str:
    """Photo backgrounds as classes, sent once per page so the live parts stay small."""
    rules = [f'.dbt-hero.pic {{background-image:url({_img("debate_athens.jpg")});}}',
             f'.dbt-win.pic {{background-image:url({_img("debate_gavel.jpg")});}}']
    for i, res in enumerate(room["settings"]["resolutions"]):
        for side in L.SIDES:
            uri = _img(res.get(f"img_{side}", ""))
            if uri:
                rules.append(f".dbt-side.r{i}.{side} {{background-image:url({uri});}}")
    return "<style>" + "\n".join(rules) + "</style>"


def _mmss(sec: float) -> str:
    s = max(0, math.ceil(sec))
    return f"{s // 60}:{s % 60:02d}"


def _dur_words(sec: float) -> str:
    m = sec / 60
    return f"{m:g} min" if sec >= 60 else f"{sec:g} s"


def clock_html(room: dict, size: str = "big", now: float | None = None) -> str:
    t = room["debate"]["timer"]
    state = L.timer_state(t, now)
    if state == "none":
        return ""
    left = L.timer_left(t, now)
    cls = "over" if state == "over" else ("hot" if left <= 10 else "warn" if left <= 30 else "")
    txt = "Time!" if state == "over" else _mmss(left)
    return (f'<div class="dbt-clock {size} {cls}" data-left="{left:.2f}" data-run="{1 if L.timer_running(t) else 0}" '
            f'data-k="{room["code"]}:{t["v"]}"><span class="t">{txt}</span></div>')


def _seg_title(room: dict, seg: dict, short: bool = False) -> str:
    if seg["side"] is None:
        return seg["label"]
    team = L.team_name(L.resolution(room)[seg["side"]])
    return f'{seg["label"]} · {team}' if not short else f'{seg["label"]} {team.replace("Team ", "T")}'


def _res_html(room: dict, phone: bool = False, track: bool = True) -> str:
    d = room["debate"]
    res = L.resolution(room)
    n = len(room["settings"]["resolutions"])
    head = f'Resolution {d["r"] + 1}' + (f' of {n}' if n > 1 else "") + (f' · {res["title"]}' if res.get("title") else "")
    chips = ""
    if track:
        parts = []
        for i, s in enumerate(L.segments(room["settings"])):
            cls = "done" if i < d["seg"] else ("on " + (s["side"] or "")) if i == d["seg"] else ""
            parts.append(f'<span class="{cls}">{_seg_title(room, s, short=True)}</span>')
        chips = f'<div class="dbt-track">{"".join(parts)}</div>'
    scene = f'<div class="scene">{res["scene"]}</div>' if res.get("scene") else ""
    right = "" if phone else (f'<span>Room {room["code"]} · <span class="addr">'
                              f'{rooms.join_url(PATH, room["code"]).split("//")[-1]}</span></span>')
    return (f'<div class="dbt-res {"phone" if phone else ""}"><div class="k"><span>{head}</span>{right}</div>{scene}'
            f'<div class="q">{res["text"]}</div>{chips}</div>')


def _rx_html(counts: dict) -> str:
    items = [f"<span>{e} {counts[k]}</span>" for k, e, _ in L.EMOJI if counts.get(k)]
    return f'<div class="rx">{"".join(items)}</div>' if items else ""


def _bar_html(c: dict, thin: bool = False, labels: bool = True) -> str:
    total = sum(c.values())
    if total == 0:
        return f'<div class="dbt-bar {"thin" if thin else ""}"><div class="lock">No panel votes yet</div></div>'
    names = {"for": "For", "und": "Not sure", "against": "Against"}
    parts = []
    for s in L.STANCES:
        if c[s]:
            txt = f"{names[s]} · {c[s]}" if (labels and not thin and c[s] / total > 0.16) else str(c[s])
            parts.append(f'<div class="{s}" style="flex:{c[s]}">{txt}</div>')
    return f'<div class="dbt-bar {"thin" if thin else ""}">{"".join(parts)}</div>'


def _panel_names(room: dict) -> str:
    ts = [L.team_name(t) for t in L.panel_teams(room)]
    if not ts:
        return "No panel"
    return ("Teams " + " and ".join(t.replace("Team ", "") for t in ts)) if len(ts) > 1 else ts[0]


def _sfx(slot, track: str | None = None, hold: float = 4.0):
    """Play a one-shot sound and keep its element on the page for a few seconds, so a redraw does not cut it."""
    now = time.time()
    if track:
        n = st.session_state.get("sfx_n", 0) + 1
        st.session_state["sfx_n"] = n
        st.session_state["dbt_sfx"] = (f'<audio autoplay preload="auto" data-n="{n}" src="{ui.sound_uri(track)}"></audio>',
                                       now + hold)
    held = st.session_state.get("dbt_sfx")
    if held and now < held[1]:
        slot.html(held[0])


def _do(code: str, fn):
    get_store().update(code, fn)
    st.rerun(scope="fragment")


# ---------------------------------------------------------------------------- board: lobby
def _teams_html(room: dict) -> str:
    cards = []
    for t in range(1, int(room["settings"]["teams"]) + 1):
        ms = L.members(room, t)
        chips = "".join(f"<span>{p['name']}</span>" for p in ms) or "<i>waiting for the first name</i>"
        cards.append(f'<div class="dbt-team" style="--c:{L.team_color(t)}"><div class="n">{L.team_name(t)}'
                     f'<small>{len(ms)} in</small></div><div class="m">{chips}</div></div>')
    return f'<div class="dbt-teams">{"".join(cards)}</div>'


def _how_html(room: dict) -> str:
    t = {**L.DEFAULT_TIMES, **room["settings"].get("times", {})}
    steps = [("Prepare", _dur_words(t["prep"])), ("Opening, each side", _dur_words(t["open"])),
             ("Rebuttal, each side", _dur_words(t["rebut"])), ("Closing, each side", _dur_words(t["close"])),
             ("The panel", "votes")]
    return '<div class="dbt-how">' + "".join(f"<div><b>{v}</b>{k}</div>" for k, v in steps) + "</div>"


def _board_lobby(room: dict, sfx_track: list):
    code = room["code"]
    s = room["settings"]
    n_res = len(s["resolutions"])
    seen = st.session_state.get("dbt_people_seen")
    st.session_state["dbt_people_seen"] = len(room["people"])
    if seen is not None and len(room["people"]) > seen:
        sfx_track.append("pop.mp3")
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        st.html(f'<div class="dbt-hero pic"><div class="in"><div class="k">Frontiers of Science · '
                f'{room.get("title") or "Seminar"}</div><h1>Debate</h1><p>{NUM[min(int(s["teams"]), 6)]} teams. '
                f'{NUM[min(n_res, 6)]} resolution{"s" if n_res != 1 else ""}.<br>Argue the side you are given.</p></div></div>')
        q, c = st.columns([1, 2.1], vertical_alignment="center")
        url = rooms.join_url(PATH, code)
        with q:
            st.image(rooms.qr_png(url), width=175)
        with c:
            st.html(f'<div class="board-code"><div><div class="code">{code}</div><div class="how"><b>Scan the code</b> or open '
                    f'<span class="url">{url.split("//")[-1]}</span><br>Type your first name and pick your team.</div></div></div>')
    with right:
        st.html(_teams_html(room))
        st.html(_how_html(room))
        a, b = st.columns([2, 1], vertical_alignment="center")
        with a:
            st.html(f'<div class="small">{len(room["people"])} joined. When everyone sits with their team, '
                    f'show the first resolution.</div>')
        with b:
            if st.button("Show Resolution 1", type="primary", icon=":material/gavel:", width="stretch", key="dbt_go"):
                _do(code, lambda r: L.start_resolution(r, 0))


# ---------------------------------------------------------------------------- board: a resolution
def _side_html(room: dict, side: str, tally: dict, now: float) -> str:
    d = room["debate"]
    res = L.resolution(room)
    seg = L.current_seg(room)
    team = res[side]
    result = d["seg"] == L.SEG_RESULT
    cls = [f"dbt-side {side} r{d['r']}"]
    badge = ""
    if seg["side"] == side:
        cls.append("live")
        badge = '<div class="badge">Speaking now</div>'
    elif seg["side"] is not None:
        cls.append("dim")
    if result and tally["winner"] == side:
        cls.append("live")
        badge = '<div class="badge">Convinced the panel</div>'
    floats = ""
    if seg["side"] == side:
        for emo, fid, age in _fresh_reactions(room, side, now):
            floats += (f'<span class="dbt-fl" style="left:{6 + (fid * 37) % 78}%; animation-delay:-{age:.2f}s">'
                       f'{L.EMOJI_CHAR[emo]}</span>')
    names = " · ".join(p["name"] for p in L.members(room, team))
    word = "For" if side == "for" else "Against"
    if result:
        sw = tally["swing"][side]
        body = (f'<div class="tag">{word} · {L.team_name(team)}</div>'
                f'<div class="big">{tally["after"][side]}<small>vote{"s" if tally["after"][side] != 1 else ""}'
                f' · {"+" if sw > 0 else ""}{sw} since the start</small></div>')
    else:
        body = (f'<div class="tag">Argues {word.lower()}</div><div class="tm">{L.team_name(team)}</div>'
                + (f'<div class="cap">{res.get("cap_" + side)}</div>' if res.get("cap_" + side) else ""))
    return (f'<div class="{" ".join(cls)}">{badge}{floats}<div class="in">{body}'
            f'<div class="mem">{names}</div>{_rx_html(tally["reacts"].get(side, {}))}</div></div>')


def _fresh_reactions(room: dict, side: str, now: float, life: float = 3.6) -> list[tuple[str, int, float]]:
    """Reactions to float on this screen: (emoji, id, seconds since this screen first showed it).
    The age counts from when the board first saw the reaction, not from the tap, so a slow connection
    still gets the whole animation. Reactions from before this page opened are not replayed."""
    key = f'dbt_seen_{room["code"]}'
    feed = room["debate"]["feed"]
    if key not in st.session_state:
        st.session_state[key] = {"from": room["debate"]["fid"], "t": {}}
    seen = st.session_state[key]
    out = []
    for _ts, emo, fside, fid in feed:
        if fid <= seen["from"]:
            continue
        first = seen["t"].setdefault(fid, now)
        if now - first < life and fside == side:
            out.append((emo, fid, now - first))
    for fid in [f for f, t in seen["t"].items() if now - t > 30]:
        del seen["t"][fid]
        seen["from"] = max(seen["from"], fid)
    return out


def _pan_html(room: dict, tally: dict) -> str:
    d = room["debate"]
    who = _panel_names(room)
    n = tally["n"]
    if d["seg"] == 0:
        bar = (f'<div class="dbt-bar"><div class="lock">🔒 {tally["picked"]} of {n} have picked a side. '
               f'The split shows when the opening starts.</div></div>')
        right = "On your phone: where do you stand before the debate?"
    elif d["seg"] == L.SEG_RESULT:
        bar = (f'<div class="dbt-rows"><span>Before</span>{_bar_html(tally["before"], thin=True)}'
               f'<span>After</span>{_bar_html(tally["after"])}</div>')
        right = f'{tally["moved"]} of {n} changed their mind'
    else:
        b = tally["before"]
        bar = _bar_html(tally["after"])
        right = (f'Before the debate: {b["for"]} for · {b["und"]} not sure · {b["against"]} against'
                 + (f' · {tally["moved"]} moved' if tally["moved"] else ""))
        if d["seg"] == L.SEG_VOTE:
            right = f'Final vote: {tally["final"]} of {n} in'
    return (f'<div class="dbt-pan"><div class="h"><b>The panel · {who}</b><span>{right}</span></div>{bar}</div>')


def _win_html(room: dict, tally: dict) -> str:
    res = L.resolution(room)
    a = tally["after"]
    if tally["n"] == 0:
        w, s = "No panel votes", "Nobody was on the panel for this resolution."
    elif tally["winner"] is None:
        w, s = "A tie", f'{a["for"]} to {a["against"]}, and nobody gained more than the other side.'
    else:
        team = L.team_name(res[tally["winner"]])
        w = f"{team} convinced the panel"
        hi, lo = max(a["for"], a["against"]), min(a["for"], a["against"])
        s = (f"{hi} to {lo}" + (f' · {a["und"]} still not sure' if a["und"] else "")) if tally["how"] == "votes" else \
            f"{hi} to {lo}: a tie on votes, won on minds changed"
    return (f'<div class="dbt-win pic"><div class="k">The panel has voted</div><div class="w">{w}</div>'
            f'<div class="s">{s}</div></div>')


def _controls(room: dict, now: float):
    code = room["code"]
    d = room["debate"]
    seg_i = d["seg"]
    segs = L.segments(room["settings"])
    state = L.timer_state(d["timer"], now)
    n_res = len(room["settings"]["resolutions"])
    last = d["r"] + 1 >= n_res
    with st.container(key="dbt_ctl"):
        if seg_i == L.SEG_RESULT:
            c = st.columns([0.7, 4.3])
            with c[0]:
                if st.button("", icon=":material/skip_previous:", key="dbt_back", width="stretch", help="Back to the final vote"):
                    _do(code, lambda r: L.go_seg(r, seg_i - 1))
            with c[1]:
                if st.button("Finish and debrief" if last else f"Show Resolution {d['r'] + 2}", type="primary",
                             key="dbt_main", width="stretch", icon=":material/arrow_forward:"):
                    _do(code, (lambda r: L.finish(r)) if last else (lambda r: L.start_resolution(r, d["r"] + 1)))
            return
        c = st.columns([0.7, 2.5, 0.7, 1.15, 0.7])
        with c[0]:
            if st.button("", icon=":material/skip_previous:", key="dbt_back", width="stretch", help="Back one step",
                         disabled=seg_i == 0):
                _do(code, lambda r: L.go_seg(r, seg_i - 1))
        with c[1]:
            if state in ("idle", "paused"):
                if st.button("Start the clock" if state == "idle" else "Resume", type="primary", key="dbt_main",
                             width="stretch", icon=":material/play_arrow:"):
                    _do(code, lambda r: L.timer_start(r["debate"]["timer"]))
            elif state == "running":
                if st.button("Pause", key="dbt_main", width="stretch", icon=":material/pause:"):
                    _do(code, lambda r: L.timer_pause(r["debate"]["timer"]))
            else:
                nxt = segs[seg_i + 1]
                label = "Count the votes" if nxt["key"] == "result" else f"Next: {_seg_title(room, nxt, short=True)}"
                if st.button(label, type="primary", key="dbt_main", width="stretch", icon=":material/arrow_forward:"):
                    _do(code, lambda r: L.go_seg(r, seg_i + 1))
        with c[2]:
            if st.button("", icon=":material/skip_next:", key="dbt_next", width="stretch", help="Next step"):
                _do(code, lambda r: L.go_seg(r, seg_i + 1))
        with c[3]:
            if st.button("+30 s", key="dbt_add", width="stretch", help="Add 30 seconds"):
                _do(code, lambda r: L.timer_add(r["debate"]["timer"], 30))
        with c[4]:
            if st.button("", icon=":material/restart_alt:", key="dbt_reset", width="stretch", help="Reset this clock",
                         disabled=state == "idle"):
                _do(code, lambda r: L.timer_reset(r["debate"]["timer"]))


def _board_run(room: dict, sfx_track: list):
    now = time.time()
    d = room["debate"]
    seg = L.current_seg(room)
    tally = L.tally(room)
    res = L.resolution(room)
    st.html(_res_html(room))
    a, mid, b = st.columns([1.22, 1, 1.22], gap="medium")
    with a:
        st.html(_side_html(room, "for", tally, now))
    with b:
        st.html(_side_html(room, "against", tally, now))
    with mid:
        if d["seg"] == L.SEG_RESULT:
            st.html(_win_html(room, tally))
        else:
            hint = {"prep": "Teams prepare. The panel picks a starting side.",
                    "vote": "Panel: which team convinced you?"}.get(seg["key"], "Panel: react, and change sides if you are moved.")
            side_cls = seg["side"] or ""
            who = L.team_name(res[seg["side"]]) if seg["side"] else ("The panel votes" if seg["key"] == "vote" else "Everyone")
            st.html(f'<div class="dbt-now"><div class="a">{seg["label"]}</div><div class="b {side_cls}">{who}</div></div>'
                    f'{clock_html(room, "big", now)}<div class="dbt-now"><div class="c">{hint}</div></div>')
        _controls(room, now)
    st.html(_pan_html(room, tally))
    # sounds: a bell when the clock runs out, a gavel and balloons when the votes are counted
    t = d["timer"]
    key = f'{room["code"]}:{t["v"]}'
    if L.timer_state(t, now) == "over" and st.session_state.get("dbt_bell") != key:
        st.session_state["dbt_bell"] = key
        sfx_track.append("bell.mp3")
    rkey = f'{room["code"]}:{d["r"]}'
    if d["seg"] == L.SEG_RESULT:
        if st.session_state.get("dbt_gavel") != rkey:
            st.session_state["dbt_gavel"] = rkey
            sfx_track.append("gavel.mp3")
            if tally["winner"]:
                st.balloons()
    elif st.session_state.get("dbt_gavel") == rkey:
        st.session_state.pop("dbt_gavel")


# ---------------------------------------------------------------------------- board: the end
def _summary_card(room: dict, r: int) -> str:
    res = room["settings"]["resolutions"][r]
    t = L.tally(room, r)
    if t["winner"]:
        head = f'{L.team_name(res[t["winner"]])} convinced the panel'
    else:
        head = "A tie" if (t["after"]["for"] or t["after"]["against"]) else "No votes"
    return (f'<div class="dbt-pan"><div class="h"><b>Resolution {r + 1} · {head}</b>'
            f'<span>{t["moved"]} of {t["n"]} changed their mind</span></div>'
            f'<div class="small" style="margin-bottom:.5rem">{res["text"]}</div>'
            f'<div class="dbt-rows"><span>Before</span>{_bar_html(t["before"], thin=True)}'
            f'<span>After</span>{_bar_html(t["after"])}</div>'
            f'<div class="small" style="margin-top:.45rem">For · {L.team_name(res["for"])} &nbsp;|&nbsp; '
            f'Against · {L.team_name(res["against"])}</div></div>')


def _debrief_html(room: dict) -> str:
    qs = [q for q in room["settings"].get("debrief", []) if q.strip()]
    if not qs:
        return ""
    return ('<div class="dbt-deb"><h2 class="vt">Debrief: now say what you really think</h2><ol>'
            + "".join(f"<li>{q}</li>" for q in qs) + "</ol></div>")


def _board_done(room: dict):
    n = len(room["settings"]["resolutions"])
    st.html(f'<div class="dbt-sum">{"".join(_summary_card(room, r) for r in range(n))}</div>')
    st.html(_debrief_html(room))
    c = st.columns([1, 1, 3])
    with c[0]:
        if st.button("Back to the lobby", key="dbt_lobby", icon=":material/groups:", width="stretch"):
            _do(room["code"], L.back_to_lobby)


@st.fragment(run_every=1)
def _board_live(code: str):
    slot = st.empty()
    room = get_store().get(code)
    if room is None:
        st.warning("This room was closed.")
        return
    tracks: list[str] = []
    stage = room["debate"]["stage"]
    if stage == "lobby":
        _board_lobby(room, tracks)
    elif stage == "run":
        _board_run(room, tracks)
    else:
        _board_done(room)
    _sfx(slot, tracks[-1] if tracks else None)


def _board_tools(room: dict):
    store = get_store()
    code = room["code"]
    with st.popover("Room", icon=":material/tune:"):
        st.caption(f"Room {code}" + (f" · {room['title']}" if room.get("title") else ""))
        n = len(room["settings"]["resolutions"])
        opts = ["Lobby"] + [f"Resolution {i + 1}" for i in range(n)] + ["Debrief"]
        go = st.selectbox("Jump to", opts, key="dbt_jump", index=None, placeholder="Jump to…")
        if go and st.button("Go", key="dbt_jump_go", icon=":material/arrow_forward:"):
            if go == "Lobby":
                store.update(code, L.back_to_lobby)
            elif go == "Debrief":
                store.update(code, L.finish)
            else:
                store.update(code, lambda r: L.start_resolution(r, opts.index(go) - 1))
            st.rerun()
        if st.button("Edit texts and times", key="dbt_edit", icon=":material/edit:"):
            _edit_dialog(code)
        if room["debate"]["stage"] == "run" and st.button("Clear this resolution's votes and reactions", key="dbt_clear",
                                                         icon=":material/restart_alt:"):
            store.update(code, lambda r: (L.reset_resolution(r, r["debate"]["r"]), L.go_seg(r, 0)))
            st.rerun()
        people = sorted(room["people"].values(), key=lambda p: (p["team"], p["name"].lower()))
        if people:
            labels = [f"{p['name']} · {L.team_name(p['team'])}" for p in people]
            pick = st.selectbox("Remove someone", labels, key="dbt_rm", index=None, placeholder="Remove someone…")
            if pick and st.button("Remove", key="dbt_rm_go", icon=":material/person_remove:"):
                pid = people[labels.index(pick)]["id"]
                store.update(code, lambda r: L.remove_person(r, pid))
                st.rerun()
        with st.expander("QR code for latecomers"):
            st.image(rooms.qr_png(rooms.join_url(PATH, code)), width=180)
        if st.button("Close this room", icon=":material/delete:", key="dbt_close"):
            store.delete_room(code)
            rooms.go()


def board(room: dict):
    c1, c2, c3 = st.columns([4.2, 0.9, 0.9], vertical_alignment="center")
    with c1:
        ui.topbar(TITLE, room.get("title") or f"Room {room['code']}")
    with c2:
        ui.music("lobby.mp3")
    with c3:
        _board_tools(room)
    st.html(_image_css(room))
    _board_live(room["code"])


# ---------------------------------------------------------------------------- phone
def _stance_buttons(room: dict, pid: str, options: list[tuple[str, str]], final: bool = False):
    code = room["code"]
    cur = (room["debate"]["votes"].get(str(room["debate"]["r"]), {}).get(pid) or {}).get("now")
    with st.container(key=f"grid_stance_{len(options)}"):
        cols = st.columns(len(options))
        for col, (s, label) in zip(cols, options):
            with col, st.container(key=f"dbt_s_{s}_{'on' if cur == s else 'off'}"):
                if st.button(label, key=f"dbt_st_{s}", width="stretch"):
                    _do(code, lambda r, s=s: L.set_stance(r, pid, s, final))


def _react(code: str, pid: str, emoji: str) -> bool:
    """Count a reaction in memory, without writing the rooms file: taps come fast, and losing a few on a restart
    does not matter. Uses the store's lock directly, so it also works with a Store object that was created
    before a code update (Streamlit Cloud can reload the code and keep the old object)."""
    store = get_store()
    with store.lock:
        room = store.rooms.get(code.upper())
        if room is None:
            return False
        ok = L.react(room, pid, emoji)
        room["updated"] = time.time()
        return ok


def _react_buttons(room: dict, pid: str, team: str):
    code = room["code"]
    for start in range(0, len(L.EMOJI), 3):                 # three to a row, so the labels stay readable on a phone
        with st.container(key=f"grid_rx_{start}"):
            cols = st.columns(3)
            for col, (k, emo, label) in zip(cols, L.EMOJI[start:start + 3]):
                with col:
                    with st.container(key=f"dbt_rx_{k}"):
                        if st.button(emo, key=f"dbt_rxb_{k}", width="stretch", help=label):
                            ok = _react(code, pid, k)
                            st.session_state["dbt_sent"] = (f"{emo} sent to {team}" if ok else "One at a time…", time.time())
                            st.rerun(scope="fragment")
                    st.html(f'<div class="dbt-cap">{label}</div>')
    sent = st.session_state.get("dbt_sent")
    st.html(f'<div class="dbt-sent">{sent[0] if sent and time.time() - sent[1] < 4 else "Tap as often as you like."}</div>')


def _now_line(room: dict, now: float) -> str:
    seg = L.current_seg(room)
    res = L.resolution(room)
    who = L.team_name(res[seg["side"]]) if seg["side"] else {"prep": "Everyone prepares", "vote": "The panel votes"}.get(seg["key"], "")
    return (f'<div class="dbt-line"><div class="l"><small>{seg["label"]}</small><b class="{seg["side"] or ""}">{who}</b></div>'
            f'{clock_html(room, "mid", now)}</div>')


def _phone_result(room: dict, me: dict, my_role: str) -> str:
    t = L.tally(room)
    res = L.resolution(room)
    a = t["after"]
    if t["winner"]:
        head = f'{L.team_name(res[t["winner"]])} convinced the panel'
    else:
        head = "A tie" if t["n"] else "No panel votes"
    extra = ""
    if my_role == "panel":
        v = room["debate"]["votes"].get(str(room["debate"]["r"]), {}).get(me["id"]) or {}
        pre, cur = L.STANCE_LABEL[v.get("pre") or "und"], L.STANCE_LABEL[v.get("now") or "und"]
        extra = f'<div class="c">You started at "{pre}" and ended at "{cur}".</div>'
    elif t["winner"]:
        extra = f'<div class="c">{"Your team won the panel." if t["winner"] == my_role else "The other team won the panel this time."}</div>'
    return (f'<div class="dbt-role panel"><div class="a">The panel has voted</div><div class="b">{head}</div>'
            f'<div class="c">For {a["for"]} · Against {a["against"]}' + (f' · Not sure {a["und"]}' if a["und"] else "")
            + f'</div>{extra}</div>')


def _phone_run(room: dict, me: dict):
    now = time.time()
    d = room["debate"]
    seg = L.current_seg(room)
    res = L.resolution(room)
    my_role = L.role(room, me["team"])
    pid = me["id"]
    st.html(_res_html(room, phone=True, track=False))
    if d["seg"] == L.SEG_RESULT:
        st.html(_phone_result(room, me, my_role))
        return
    st.html(_now_line(room, now))
    if my_role in L.SIDES:
        word = "FOR" if my_role == "for" else "AGAINST"
        st.html(f'<div class="dbt-role {my_role}"><div class="a">{L.team_name(me["team"])} argues</div><div class="b">{word}</div>'
                f'<div class="c">Argue the side you are given, with evidence.</div></div>')
        if seg["key"] == "prep":
            msg, you = "Prepare your case with your team.", False
        elif seg["key"] == "vote":
            msg, you = "The panel is voting. Well done.", False
        elif seg["side"] == my_role:
            msg, you = f'Your team is speaking: {seg["label"].lower()}.', True
        else:
            msg, you = "Listen to the other team. Note what you will answer.", False
        st.html(f'<div class="dbt-turn {"you" if you else ""}">{msg}</div>')
        hint = res.get(f"hint_{my_role}")
        if hint:
            with st.expander("Stuck? Some ideas for your side"):
                st.write(hint)
        return
    # the panel
    if seg["key"] == "prep":
        st.html('<div class="p-head">Before the debate: where do you stand?</div>')
        _stance_buttons(room, pid, [("for", "For"), ("und", "Not sure"), ("against", "Against")])
        st.html('<div class="small">Nobody sees your choice. The board shows only the totals, once the opening starts.</div>')
    elif seg["key"] == "vote":
        st.html('<div class="p-head">Final vote: which team convinced you?</div>')
        _stance_buttons(room, pid, [("for", f'{L.team_name(res["for"])} · For'),
                                    ("against", f'{L.team_name(res["against"])} · Against')], final=True)
        v = d["votes"].get(str(d["r"]), {}).get(pid) or {}
        st.html('<div class="saved">Your vote is in. You can change it until the votes are counted.</div>' if v.get("final")
                else '<div class="small">Vote for the team that argued better, not for the side you like.</div>')
    else:
        team = L.team_name(res[seg["side"]])
        st.html(f'<div class="p-head">React to {team}</div>')
        _react_buttons(room, pid, team)
        st.html('<div class="p-head">Your side right now</div>')
        _stance_buttons(room, pid, [("for", "For"), ("und", "Not sure"), ("against", "Against")])
        st.html('<div class="small">Moved by an argument? Change sides any time.</div>')


@st.fragment(run_every=2)
def _phone_live(code: str, pid: str):
    room = get_store().get(code)
    if room is None:
        st.warning("This room was closed.")
        return
    me = room["people"].get(pid)
    if me is None:
        st.info("You are no longer in this room. Reload the page to join again.")
        return
    stage = room["debate"]["stage"]
    if stage == "lobby":
        mates = [p["name"] for p in L.members(room, me["team"]) if p["id"] != pid]
        st.html(f'<div class="dbt-role panel"><div class="a">You are in</div><div class="b">{L.team_name(me["team"])}</div>'
                f'<div class="c">Sit with your team and watch the screen.'
                + (f'<br>With you: {", ".join(mates)}' if mates else "") + '</div></div>')
    elif stage == "run":
        _phone_run(room, me)
    else:
        st.html('<div class="dbt-role panel"><div class="a">Debate over</div><div class="b">Thank you</div>'
                '<div class="c">Now say what you really think.</div></div>')
        st.html(_debrief_html(room))


def _join_form(room: dict):
    code = room["code"]
    store = get_store()
    st.html(f'<div class="dbt-hero pic small"><div class="in"><div class="k">Room {code}'
            f'{(" · " + room["title"]) if room.get("title") else ""}</div><h1>Debate</h1>'
            f'<p>Type your first name and pick your team.</p></div></div>')
    name = st.text_input("Your first name", key="dbt_name", placeholder="First name", max_chars=24)
    existing = room["people"].get(L.person_id(name)) if name.strip() else None
    if existing and "dbt_team" not in st.session_state:
        st.session_state["dbt_team"] = existing["team"]
    chosen = st.session_state.get("dbt_team")
    st.html('<div class="p-head">Your team</div>')
    teams = list(range(1, int(room["settings"]["teams"]) + 1))
    for start in range(0, len(teams), 2):
        row = teams[start:start + 2]
        with st.container(key=f"grid_team_{start}"):
            cols = st.columns(2)
            for col, t in zip(cols, row):
                with col, st.container(key=f"dbt_t_{t}_{'on' if chosen == t else 'off'}"):
                    st.html(f'<style>[class*="st-key-dbt_t_{t}_"] button{{border-left:10px solid {L.team_color(t)} !important}}</style>')
                    if st.button(f"{L.team_name(t)} · {len(L.members(room, t))} in", key=f"dbt_pick_{t}", width="stretch"):
                        st.session_state["dbt_team"] = t
                        st.rerun()
    if existing:
        st.info(f"Welcome back, {existing['name']}. If you are a different {existing['name']}, add the first letter "
                f"of your last name.", icon=":material/history:")
    if st.button("Join", type="primary", icon=":material/login:", width="stretch", disabled=not (name.strip() and chosen)):
        out = []
        store.update(code, lambda r: out.append(L.join(r, name, chosen)))
        pid, err = out[0] if out else (None, "That room does not exist any more.")
        if err:
            st.html(f'<div class="err">{err}</div>')
        else:
            st.query_params["me"] = pid
            st.rerun()


def phone(room: dict):
    pid = st.query_params.get("me")
    me = room["people"].get(pid) if pid else None
    st.html(f'<style>.dbt-hero.pic {{background-image:url({_img("debate_athens_s.jpg")});}}</style>')
    if me is None:
        _join_form(room)
        return
    with st.container(key="grid_me"):
        a, b = st.columns([2.4, 1], vertical_alignment="center")
    with a:
        st.html(f'<div class="dbt-me" style="--c:{L.team_color(me["team"])}">{me["name"]}<span>{L.team_name(me["team"])}</span></div>')
    with b:
        if st.button("Change", key="dbt_chg", width="stretch", help="Change your name or team"):
            st.session_state["dbt_name"] = me["name"]
            st.session_state["dbt_team"] = me["team"]
            del st.query_params["me"]
            st.rerun()
    _phone_live(room["code"], pid)


# ---------------------------------------------------------------------------- settings: at the start, and later
def _time_fields(times: dict, key: str):
    spec = [("prep", "Prepare (min)", 60), ("open", "Opening (min)", 60), ("rebut", "Rebuttal (min)", 60),
            ("close", "Closing (min)", 60), ("vote", "Vote (s)", 1)]
    for col, (k, label, unit) in zip(st.columns(5), spec):
        with col:
            v = st.number_input(label, 0.5 if unit == 60 else 10.0, 30.0 if unit == 60 else 180.0,
                                float(times.get(k, L.DEFAULT_TIMES[k]) / unit), step=0.5 if unit == 60 else 5.0,
                                key=f"dbt_time_{k}_{key}")
            times[k] = int(round(v * unit))


def _resolution_fields(res: dict, i: int, teams: int, key: str, expanded: bool = False) -> list[str]:
    tnames = list(range(1, teams + 1))
    with st.expander(f"Resolution {i + 1}" + (f" · {res['title']}" if res["title"] else ""), expanded=expanded or not res["text"]):
        res["title"] = st.text_input("Short title", res["title"], key=f"dbt_title_{key}", placeholder="You are the funding panel")
        res["scene"] = st.text_input("The setting, one line", res["scene"], key=f"dbt_scene_{key}")
        res["text"] = st.text_area("The resolution", res["text"], key=f"dbt_text_{key}", height=90,
                                   placeholder="A statement one team argues for and one team argues against.")
        a, b = st.columns(2)
        with a:
            res["for"] = st.selectbox("Argues for", tnames, index=min(res["for"], teams) - 1, key=f"dbt_for_{key}_{teams}",
                                      format_func=L.team_name)
            res["hint_for"] = st.text_area("Ideas if they are stuck (shown on their phones)", res["hint_for"],
                                           key=f"dbt_hf_{key}", height=110)
        with b:
            res["against"] = st.selectbox("Argues against", tnames, index=min(res["against"], teams) - 1,
                                          key=f"dbt_against_{key}_{teams}", format_func=L.team_name)
            res["hint_against"] = st.text_area("Ideas if they are stuck (shown on their phones)", res["hint_against"],
                                               key=f"dbt_ha_{key}", height=110)
    problems = []
    if not res["text"].strip():
        problems.append(f"Resolution {i + 1} needs its text.")
    if res["for"] == res["against"]:
        problems.append(f"Resolution {i + 1}: one team cannot argue both sides.")
    return problems


def _setup() -> tuple[dict, list[str]]:
    """The settings form on the start page. Returns (settings, problems)."""
    preset = st.selectbox("Start from", ["ml2", "blank"], key="dbt_preset",
                          format_func=lambda k: L.ML2["label"] if k == "ml2" else "Blank: write your own resolutions")
    c = st.columns(2)
    with c[0]:
        teams = int(st.number_input("Teams", 3, 6, 4, key="dbt_teams",
                                    help="Two teams debate each resolution. The others are the panel."))
    with c[1]:
        n_res = int(st.number_input("Resolutions", 1, 4, 2, key=f"dbt_nres_{preset}"))
    s = L.default_settings(preset, teams, n_res)
    st.html('<div class="small">Every text and every time below can be changed, now or later from the Room menu on the board.</div>')
    with st.expander("Speaking times"):
        _time_fields(s["times"], "new")
    problems = []
    for i, res in enumerate(s["resolutions"]):
        problems += _resolution_fields(res, i, teams, f"{preset}_{i}")
    with st.expander("Debrief questions"):
        txt = st.text_area("One per line", "\n".join(s["debrief"]), key=f"dbt_debrief_{preset}", height=110)
        s["debrief"] = [q.strip() for q in txt.splitlines() if q.strip()]
    return s, problems


@st.dialog("Edit the debate", width="large")
def _edit_dialog(code: str):
    """Change texts and times while the room is open. Votes and reactions are kept."""
    import copy

    store = get_store()
    room = store.get(code)
    if room is None:
        st.warning("This room was closed.")
        return
    s = copy.deepcopy(room["settings"])
    teams = int(s["teams"])
    st.caption("Phones and the board pick up the new text within two seconds. A clock that is already on the screen "
               "keeps its time; the new times apply from the next step, or press the reset button under the clock.")
    st.html('<div class="p-head">Times</div>')
    _time_fields(s["times"], f"ed_{code}")
    problems = []
    cur = room["debate"]["r"] if room["debate"]["stage"] == "run" else -1
    for i, res in enumerate(s["resolutions"]):
        problems += _resolution_fields(res, i, teams, f"ed_{code}_{i}", expanded=(i == cur))
    with st.expander("Debrief questions"):
        txt = st.text_area("One per line", "\n".join(s.get("debrief", [])), key=f"dbt_debrief_ed_{code}", height=110)
        s["debrief"] = [q.strip() for q in txt.splitlines() if q.strip()]
    for p in problems:
        st.html(f'<div class="err">{p}</div>')
    if st.button("Save", type="primary", icon=":material/save:", disabled=bool(problems)):
        store.update(code, lambda r: L.apply_settings(r, s))
        st.rerun()


def landing():
    store = get_store()
    store.sweep()
    st.html(f'<style>.dbt-hero.pic {{background-image:url({_img("debate_athens.jpg")});}}</style>')
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        st.html('<div class="card"><h2 class="vt">Start a debate</h2><p class="lede">Two teams argue each resolution, for and '
                'against. Everybody else is the panel: they pick a side before the opening, react to each speech from '
                'their phones, change sides when an argument moves them, and vote at the end. The board keeps the clock.</p></div>')
        name = st.text_input("Room name", placeholder="Section 22", key="dbt_room_name")
        settings, problems = _setup()
        for p in problems:
            st.html(f'<div class="small">{p}</div>')
        if st.button("Start the room", type="primary", icon=":material/rocket_launch:", disabled=bool(problems)):
            room = store.create_room(KIND, settings, title=name.strip())
            store.update(room["code"], L.init_room)
            rooms.go(room=room["code"], board=1)
    with right:
        st.html('<div class="dbt-hero pic small"><div class="in"><div class="k">Frontiers of Science</div><h1>Debate</h1>'
                '<p>Argue the side you are given.</p></div></div>')
        rs = store.rooms_of(KIND)
        st.html('<div class="card"><h2 class="vt">Open a room from the last 24 hours</h2>'
                + ('<p class="small">No rooms yet.</p>' if not rs else '') + '</div>')
        for room in rs[:8]:
            when = time.strftime("%a %H:%M", time.localtime(room["updated"]))
            a, b = st.columns([3, 1.2], vertical_alignment="center")
            with a:
                st.html(f'<div><b style="font-family:Barlow Condensed;font-size:1.3rem;letter-spacing:.1em">{room["code"]}</b>'
                        f' &nbsp;{room.get("title") or ""}<br><span class="small">{len(room.get("people", {}))} joined · {when}</span></div>')
            with b:
                if st.button("Open board", key=f"dbt_open_{room['code']}", width="stretch"):
                    rooms.go(room=room["code"], board=1)
        st.html('<div class="dbt-credit">Pictures: Raphael, The School of Athens (1509 to 1511), public domain. Screening, '
                'laboratory and clinic photographs: National Cancer Institute, public domain. Gavel: Smithsonian American '
                'Art Museum, CC0. All through Wikimedia Commons.</div>')


# ---------------------------------------------------------------------------- page
def render():
    _base()
    store = get_store()
    code = st.query_params.get("room")
    room = store.get(code)
    if room is not None and (room.get("kind") != KIND or "debate" not in room):
        room = None
    if code and room is None:
        ui.topbar(TITLE)
        st.warning("That room does not exist or has expired. Rooms are kept for 24 hours.")
        if st.button("Start a new room"):
            rooms.go()
        return
    if room and st.query_params.get("board"):
        board(room)
        return
    if room:
        ui.topbar(TITLE, room.get("title") or "")
        phone(room)
        return
    ui.topbar(TITLE, "Two teams argue, the panel decides")
    landing()
