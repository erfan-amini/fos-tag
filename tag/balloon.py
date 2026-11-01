"""Ballooniverse: each pair adds three dots to the class graph of velocity against distance."""
from __future__ import annotations

import time

import streamlit as st

from tag import export, plots, rooms, ui
from tag.stats import fit_through_origin, fmt
from tag.store import get_store

PATH = "ballooniverse"
KIND = "balloon"
TITLE = "Ballooniverse"
BLURB = ("Each pair draws a home and three dots on a balloon, measures the distances, inflates for a fixed time, and "
         "measures again. They send the numbers from a phone. Every dot lands on the class graph of velocity against "
         "final distance, with the trend line Hubble found.")


def _settings():
    t = st.number_input("Inflation time (seconds)", min_value=1, max_value=60, value=10, step=1,
                        help="The worksheet says 10 s. Velocity = (final − initial) ÷ this time.")
    return {"inflate_s": int(t)}


# ---------------------------------------------------------------------------- board
@st.cache_data(show_spinner=False)
def _workbook(code: str, updated: float) -> bytes:
    return export.balloon_workbook(get_store().get(code))


def _stats_html(rows: list[dict], t: float) -> str:
    f = fit_through_origin([r["final"] for r in rows], [r["v"] for r in rows])
    pairs = len({r["pair"] for r in rows})
    cards = [f'<div class="stat"><div class="t">Dots on the graph</div><div class="v">{len(rows)}</div>'
             f'<div class="s">from {pairs} {"pair" if pairs == 1 else "pairs"} · inflated {t:g} s</div></div>']
    if f["n"] >= 2:
        cards.append(f'<div class="stat"><div class="t">Best-fit line, through the origin</div><div class="v" style="font-size:1.35rem">slope = {fmt(f["k"], 3)} per second</div>'
                     f'<div class="s">velocity = slope × distance · R² = {fmt(f["r2"], 2)}</div></div>')
        cards.append(f'<div class="stat"><div class="t">What it says</div><div class="v" style="font-size:1.15rem">'
                     f'Twice as far, twice as fast</div><div class="s">velocity is proportional to distance</div></div>')
    else:
        cards.append('<div class="stat"><div class="t">Trend</div><div class="v">–</div><div class="s">needs two dots</div></div>')
    return f'<div class="stat-row">{"".join(cards)}</div>'


@st.fragment(run_every=2)
def _live_stats(code: str):
    room = get_store().get(code)
    if room is None:
        return
    t = float(room["settings"].get("inflate_s", 10) or 10)
    st.html(_stats_html(plots.balloon_points(room), t))


@st.fragment(run_every=2)
def _live_board(code: str):
    sfx = st.empty()
    room = get_store().get(code)
    if room is None:
        st.warning("This room was closed.")
        return
    rows = plots.balloon_points(room)
    rooms.pop_on_new(room, sfx)
    trend = st.session_state.get("trend", True)
    t = float(room["settings"].get("inflate_s", 10) or 10)
    st.plotly_chart(plots.balloon_figure(rows, trend=trend, big=True, t=t), width="stretch", config={"displayModeBar": False},
                    key=f"bal_fig_{code}")
    c1, c2, c3 = st.columns([1.1, 3.2, 1.1], vertical_alignment="center")
    with c1:
        st.toggle("Best-fit line", value=trend, key="trend", help="Least-squares line through the origin: velocity = slope × distance")
    with c2:
        st.html(rooms.joined_html(room))
    with c3:
        name = f"FoS_Ballooniverse_{code}_{time.strftime('%Y%m%d')}.xlsx"
        st.download_button("Export to Excel", _workbook(code, room["updated"]), file_name=name, icon=":material/download:",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch",
                           key=f"dl_{code}", disabled=not rows)


def board(room: dict):
    c1, c2, c3 = st.columns([4.2, 0.9, 0.9], vertical_alignment="center")
    with c1:
        ui.topbar(TITLE, room.get("title") or f"Room {room['code']}")
    with c2:
        ui.music("lobby.mp3")
    with c3:
        rooms.board_tools(room, PATH)
    html, url = rooms.board_code_html(PATH, room["code"])
    a, b = st.columns([1.55, 2.2], vertical_alignment="center", gap="large")
    with a:
        q, c = st.columns([1, 2.3], vertical_alignment="center")
        with q:
            st.image(rooms.qr_png(url), width=165)
        with c:
            st.html(html)
    with b:
        _live_stats(room["code"])
    _live_board(room["code"])


# ---------------------------------------------------------------------------- pair entry
def _row(label: str, key: str, saved: list | None, hint: str = "") -> tuple[float | None, float | None]:
    for i, k in enumerate((f"{key}_i", f"{key}_f")):
        if k not in st.session_state:
            st.session_state[k] = (saved or [None, None])[i]
    st.html(f'<div class="small" style="margin-top:.2rem"><b>{label}</b>{(" · " + hint) if hint else ""}</div>')
    with st.container(key=f"grid_{key}"):
        c1, c2 = st.columns(2)
        with c1:
            a = st.number_input("Initial (mm)", min_value=0.0, max_value=1000.0, step=1.0, format="%.0f", key=f"{key}_i",
                                placeholder="initial mm", label_visibility="collapsed")
        with c2:
            b = st.number_input("Final (mm)", min_value=0.0, max_value=1000.0, step=1.0, format="%.0f", key=f"{key}_f",
                                placeholder="final mm", label_visibility="collapsed")
    return a, b


@st.fragment(run_every=3)
def _mini_board(code: str):
    room = get_store().get(code)
    if room:
        rows = plots.balloon_points(room)
        t = float(room["settings"].get("inflate_s", 10) or 10)
        st.html(f'<div class="small">Class graph · {len(rows)} dots so far</div>')
        st.plotly_chart(plots.balloon_figure(rows, trend=True, big=False, t=t), width="stretch",
                        config={"displayModeBar": False, "staticPlot": True}, key=f"mini_{code}")


def entry(room: dict, pair: dict):
    rooms.pair_header(room, pair, TITLE)
    t = float(room["settings"].get("inflate_s", 10) or 10)
    st.html(f'<p class="lede">Distances from home along the balloon, before and after inflating for <b>{t:g} s</b>. '
            f'The app works out the change and the velocity.</p>')
    d = pair.get("data") or {}
    init, final = [], []
    for i, (lab, hint) in enumerate((("Dot 1", "near"), ("Dot 2", "middle"), ("Dot 3", "far"))):
        a, b = _row(lab, f"bl_{i}", [d.get("init", [None] * 3)[i], d.get("final", [None] * 3)[i]], hint)
        init.append(a)
        final.append(b)
    wa, wb = _row("Wavy line", "bl_w", d.get("wavy"), "its length")
    rows = []
    for i in range(3):
        if init[i] is not None and final[i] is not None:
            ch = final[i] - init[i]
            rows.append(f'<tr><td>Dot {i + 1}</td><td>{init[i]:.0f}</td><td>{final[i]:.0f}</td><td>{ch:+.0f}</td><td><b>{ch / t:.2f}</b></td></tr>')
    if rows:
        st.html('<div class="mean-line"><table style="width:100%;font-size:.95rem;border-collapse:collapse">'
                '<tr style="color:var(--muted);font-size:.8rem;text-transform:uppercase"><th style="text-align:left">Mark</th>'
                '<th>Initial</th><th>Final</th><th>Change</th><th>mm/s</th></tr>' + "".join(rows) + "</table></div>")
    ok = sum(1 for i in range(3) if init[i] is not None and final[i] is not None)
    if st.button("Save to the board", type="primary", icon=":material/cloud_upload:", width="stretch", disabled=ok == 0):
        get_store().submit(room["code"], pair["id"], {"init": init, "final": final, "wavy": [wa, wb]})
        st.rerun()
    if ok == 0:
        st.html('<div class="small">Enter the initial and final distance for at least one dot.</div>')
    if pair.get("data"):
        when = time.strftime("%H:%M", time.localtime(pair.get("updated", time.time())))
        st.html(f'<div class="saved">Saved at {when}. Your dots are on the class graph. Change a number and save again if you need to.</div>')
    _mini_board(room["code"])


# ---------------------------------------------------------------------------- page
def render():
    ui.base()
    store = get_store()
    code = st.query_params.get("room")
    room = store.get(code)
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
        pair = rooms.current_pair(room)
        if pair:
            entry(room, pair)
        else:
            rooms.join_form(room, PATH)
        return
    ui.topbar(TITLE, "Physics and Peace")
    rooms.landing(KIND, PATH, TITLE, BLURB, _settings)
