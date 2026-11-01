"""Two-Point Threshold: pairs send thumb and forearm readings; the board builds the class dot plots."""
from __future__ import annotations

import time

import streamlit as st

from tag import export, icons, plots, rooms, ui
from tag.stats import fmt, overlap, summary
from tag.store import get_store

PATH = "two-point"
KIND = "tpt"
TITLE = "Two-Point Threshold"
BLURB = ("Each pair measures the smallest distance at which two points still feel like two, on the thumb and on the "
         "forearm, three trials each. They send the numbers from a phone. The board shows every reading, the class "
         "means and the 95% intervals as they arrive.")


# ---------------------------------------------------------------------------- board
@st.cache_data(show_spinner=False)
def _workbook(code: str, updated: float) -> bytes:
    return export.tpt_workbook(get_store().get(code))


def _stats_html(rows: list[dict]) -> str:
    th, fa = summary([r["thumb"] for r in rows]), summary([r["forearm"] for r in rows])
    cards = []
    for name, s in (("Thumb", th), ("Forearm", fa)):
        if s["n"] == 0:
            cards.append(f'<div class="stat"><div class="t">{name}</div><div class="v">–</div><div class="s">no readings yet</div></div>')
        else:
            cards.append(f'<div class="stat"><div class="t">{name} · n = {s["n"]}</div><div class="v">{fmt(s["mean"], 1)} mm</div>'
                         f'<div class="s">SD {fmt(s["sd"], 1)} · SE {fmt(s["se"], 2)} · 95%: {fmt(s["lo"], 1)} to {fmt(s["hi"], 1)}</div></div>')
    ov = overlap(th, fa)
    if ov is None:
        v = '<div class="verdict">The verdict appears once both parts have at least two readings.</div>'
    elif ov:
        v = ('<div class="verdict no"><b>The 95% intervals overlap.</b> On this sample we cannot call the difference '
             'statistically significant.</div>')
    else:
        v = ('<div class="verdict yes"><b>The 95% intervals do not overlap.</b> The forearm threshold is larger than the thumb, '
             'and the difference is statistically significant.</div>')
    return f'<div class="stat-row">{"".join(cards)}</div>{v}'


@st.fragment(run_every=2)
def _live_stats(code: str):
    room = get_store().get(code)
    if room is None:
        return
    st.html(_stats_html(plots.tpt_people(room)))


@st.fragment(run_every=2)
def _live_board(code: str):
    sfx = st.empty()
    room = get_store().get(code)
    if room is None:
        st.warning("This room was closed.")
        return
    rows = plots.tpt_people(room)
    rooms.pop_on_new(room, sfx)
    st.plotly_chart(plots.tpt_figure(rows, big=True), width="stretch", config={"displayModeBar": False},
                    key=f"tpt_fig_{code}")
    c1, c2 = st.columns([4, 1.1], vertical_alignment="center")
    with c1:
        st.html(rooms.joined_html(room))
    with c2:
        name = f"FoS_TwoPoint_{code}_{time.strftime('%Y%m%d')}.xlsx"
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
def _trial_row(label: str, keys: list[str]) -> list[float | None]:
    st.html(f'<div class="small" style="margin-top:.2rem"><b>{label}</b> · three trials, in mm</div>')
    with st.container(key=f"grid_{keys[0]}"):
        cols = st.columns(3)
        vals = []
        for i, (col, k) in enumerate(zip(cols, keys)):
            with col:
                vals.append(st.number_input(f"Trial {i + 1}", min_value=0.0, max_value=300.0, step=0.5, format="%.1f",
                                            key=k, label_visibility="collapsed", placeholder=f"trial {i + 1}"))
    return vals


def _person_block(slot: int, default_name: str, saved: dict | None) -> dict:
    nk = f"tp_name_{slot}"
    st.session_state.setdefault(nk, (saved or {}).get("name", default_name))
    for part in ("thumb", "forearm"):
        for i in range(3):
            k = f"tp_{slot}_{part}_{i}"
            if k not in st.session_state:
                vals = (saved or {}).get(part, [None, None, None])
                st.session_state[k] = vals[i] if i < len(vals) else None
    st.html(f'<div class="p-head">Participant {slot + 1}</div>')
    name = st.text_input("Name", key=nk, placeholder="Name" if slot == 0 else "Name (leave empty if there is no second participant)")
    th = _trial_row("Thumb", [f"tp_{slot}_thumb_{i}" for i in range(3)])
    fa = _trial_row("Forearm", [f"tp_{slot}_forearm_{i}" for i in range(3)])
    tv, fv = [v for v in th if v is not None], [v for v in fa if v is not None]
    st.html(f'<div class="mean-line">Thumb <b>{fmt(sum(tv) / len(tv), 2) if tv else "–"}</b> mm &nbsp;·&nbsp; '
            f'Forearm <b>{fmt(sum(fv) / len(fv), 2) if fv else "–"}</b> mm</div>')
    return {"name": name.strip(), "thumb": th, "forearm": fa}


@st.fragment(run_every=3)
def _mini_board(code: str):
    room = get_store().get(code)
    if room:
        rows = plots.tpt_people(room)
        st.html(f'<div class="small">Class board · {len(rows)} readings so far</div>')
        st.plotly_chart(plots.tpt_figure(rows, big=False), width="stretch", config={"displayModeBar": False, "staticPlot": True},
                        key=f"mini_{code}")


def entry(room: dict, pair: dict):
    rooms.pair_header(room, pair, TITLE)
    st.html('<p class="lede">Enter the smallest distance at which your partner felt two points, for each trial. '
            'Blank trials are left out of the mean.</p>')
    saved = (pair.get("data") or {}).get("people", [])
    names = pair["names"] + [""]
    people = [_person_block(0, names[0], saved[0] if len(saved) > 0 else None),
              _person_block(1, names[1], saved[1] if len(saved) > 1 else None)]
    problems = []
    keep = []
    for i, p in enumerate(people):
        has = any(v is not None for v in p["thumb"]) or any(v is not None for v in p["forearm"])
        if not p["name"] and has:
            problems.append(f"Participant {i + 1} has numbers but no name.")
        if p["name"]:
            if not any(v is not None for v in p["thumb"]) or not any(v is not None for v in p["forearm"]):
                problems.append(f"{p['name']} needs at least one thumb and one forearm reading.")
            keep.append(p)
    if not keep:
        problems.append("Enter at least one participant.")
    if st.button("Save to the board", type="primary", icon=":material/cloud_upload:", width="stretch", disabled=bool(problems)):
        get_store().submit(room["code"], pair["id"], {"people": keep})
        st.session_state["tp_saved"] = time.time()
        st.rerun()
    for pr in problems:
        st.html(f'<div class="small">{pr}</div>')
    if pair.get("data"):
        when = time.strftime("%H:%M", time.localtime(pair.get("updated", time.time())))
        st.html(f'<div class="saved">Saved at {when}. Your readings are on the board. You can change a number and save again.</div>')
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
    ui.topbar(TITLE, "Mind and Brain")
    rooms.landing(KIND, PATH, TITLE, BLURB)
