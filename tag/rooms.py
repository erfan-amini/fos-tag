"""Pieces shared by the two live-data activities: starting rooms, the code and QR,
joining as a pair with a symbol and a colour, and the list of who is in."""
from __future__ import annotations

import io
import time
from urllib.parse import urlsplit

import qrcode
import streamlit as st

from tag import icons, ui
from tag.store import get_store


def app_origin() -> str:
    """scheme://host of the running app, as the browser sees it."""
    try:
        u = urlsplit(st.context.url)
        return f"{u.scheme}://{u.netloc}"
    except Exception:
        return ""


def join_url(path: str, code: str) -> str:
    return f"{app_origin()}/{path}?room={code}"


@st.cache_data(show_spinner=False)
def qr_png(url: str) -> bytes:
    q = qrcode.QRCode(box_size=10, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url)
    q.make(fit=True)
    im = q.make_image(fill_color="#0C2340", back_color="white")
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def go(**params):
    """Replace the query string and rerun."""
    st.query_params.clear()
    for k, v in params.items():
        if v is not None:
            st.query_params[k] = str(v)
    st.rerun()


# ---------------------------------------------------------------------------- landing
def landing(kind: str, path: str, title: str, blurb: str, settings_ui=None):
    """Start a new room or reopen one. settings_ui() may return a dict of room settings."""
    store = get_store()
    store.sweep()
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.html(f'<div class="card"><h2 class="vt">Start a room</h2><p class="lede">{blurb}</p></div>')
        name = st.text_input("Room name", placeholder="Section 22", help="Shown on the board and in the export")
        settings = settings_ui() if settings_ui else {}
        if st.button("Start the room", type="primary", icon=":material/rocket_launch:"):
            room = store.create_room(kind, settings, title=name.strip())
            go(room=room["code"], board=1)
    with right:
        rooms = store.rooms_of(kind)
        st.html('<div class="card"><h2 class="vt">Open a room from the last 24 hours</h2>'
                + ('<p class="small">No rooms yet.</p>' if not rooms else '') + '</div>')
        for room in rooms[:8]:
            n = len(room["pairs"])
            done = sum(1 for p in room["pairs"].values() if p.get("data"))
            when = time.strftime("%a %H:%M", time.localtime(room["updated"]))
            a, b = st.columns([3, 1.2], vertical_alignment="center")
            with a:
                st.html(f'<div><b style="font-family:Barlow Condensed;font-size:1.3rem;letter-spacing:.1em">{room["code"]}</b>'
                        f' &nbsp;{room.get("title") or ""}<br><span class="small">{n} pairs joined, {done} sent data · {when}</span></div>')
            with b:
                if st.button("Open board", key=f"open_{room['code']}", width="stretch"):
                    go(room=room["code"], board=1)


# ---------------------------------------------------------------------------- board pieces
def board_code_html(path: str, code: str) -> tuple[str, str]:
    url = join_url(path, code)
    short = url.replace("https://", "").replace("http://", "")
    html = (f'<div class="board-code"><div><div class="code">{code}</div><div class="how">'
            f'<b>Scan the code</b> or open <span class="url">{short}</span><br>'
            f'Type your names, pick a colour and a symbol, enter your numbers.</div></div></div>')
    return html, url


def joined_html(room: dict) -> str:
    chips = []
    for pid in room["order"]:
        p = room["pairs"].get(pid)
        if not p:
            continue
        cls = "pr" if p.get("data") else "pr wait"
        chips.append(f'<span class="{cls}">{icons.svg(p["icon"], p["color"], 20)}{p["label"]}</span>')
    if not chips:
        return '<div class="joined"><span class="small">Nobody has joined yet. The first pair to scan the code appears here.</span></div>'
    n = len(chips)
    done = sum(1 for pid in room["order"] if room["pairs"].get(pid, {}).get("data"))
    return (f'<div class="joined"><span class="pill ok">{done} of {n} sent data</span>{"".join(chips)}</div>')


def board_tools(room: dict, path: str):
    """Room-level actions in a popover: remove a pair, clear, close."""
    store = get_store()
    with st.popover("Room", icon=":material/tune:"):
        st.caption(f"Room {room['code']}" + (f" · {room['title']}" if room.get("title") else ""))
        pairs = [room["pairs"][pid] for pid in room["order"] if pid in room["pairs"]]
        if pairs:
            pick = st.selectbox("Remove a pair", ["–"] + [p["label"] for p in pairs], key="rm_pick")
            if pick != "–" and st.button("Remove", key="rm_btn", icon=":material/person_remove:"):
                pid = next(p["id"] for p in pairs if p["label"] == pick)
                store.remove_pair(room["code"], pid)
                st.rerun()
        if st.button("Close this room", icon=":material/delete:", key="close_room"):
            store.delete_room(room["code"])
            go()


def pop_on_new(room: dict, sfx):
    """A small pop on the board when a pair joins or sends data. Needs one click on the page first (browser rule)."""
    stamp = (len(room["pairs"]), sum(1 for p in room["pairs"].values() if p.get("data")))
    prev = st.session_state.get("pop_seen")
    st.session_state["pop_seen"] = stamp
    if prev is not None and stamp != prev and (stamp[0] > prev[0] or stamp[1] > prev[1]):
        ui.play(sfx, "pop.mp3")


# ---------------------------------------------------------------------------- pair join
def _tile_grid(keys: list[str], chosen: str | None, taken: dict, color: str, row_len: int):
    """Symbol tiles that stay in rows on a phone."""
    for start in range(0, len(keys), row_len):
        row = keys[start:start + row_len]
        with st.container(key=f"grid_sym_{start}"):
            cols = st.columns(len(row))
            for col, k in zip(cols, row):
                state = "taken" if k in taken else ("on" if k == chosen else "off")
                with col, st.container(key=f"tile_{k}_{state}"):
                    st.html(f'<div class="tile-in">{icons.svg(k, color if state != "taken" else "#B8C0CC", 40)}'
                            f'<div class="tile-name">{icons.LABEL[k]}</div></div>')
                    # the button is invisible and covers the whole tile, so a tap on the symbol works too
                    if st.button(icons.LABEL[k], key=f"pick_{k}", disabled=(state == "taken"), width="stretch",
                                 help=f"Taken by {taken[k]}" if k in taken else None):
                        st.session_state["sym"] = k
                        st.rerun()


def _swatches(chosen: str):
    names = [n for n, _ in icons.PALETTE]
    for start in range(0, len(names), 6):
        row = names[start:start + 6]
        with st.container(key=f"grid_col_{start}"):
            cols = st.columns(len(row))
            for col, n in zip(cols, row):
                h = icons.COLORS[n]
                with col, st.container(key=f"sw_{n}_{'on' if h == chosen else 'off'}"):
                    st.html(f'<style>[class*="st-key-sw_{n}_"] button{{background:{h} !important;color:{h} !important}}</style>')
                    if st.button(n, key=f"col_{n}", help=n, width="stretch"):
                        st.session_state["col"] = h
                        st.rerun()


def join_form(room: dict, path: str) -> dict | None:
    """Names, symbol, colour. Returns the pair once joined (also sets ?pair=)."""
    store = get_store()
    st.html(f'<div class="card"><h2 class="vt">Join room {room["code"]}'
            f'{(" · " + room["title"]) if room.get("title") else ""}</h2>'
            f'<p class="lede">Type your names, pick a colour, then a symbol. That is how you show on the board.</p></div>')
    n1 = st.text_input("Your name", key="n1", placeholder="First name")
    n2 = st.text_input("Partner's name", key="n2", placeholder="First name (leave empty if you work alone)")
    names = [n1, n2]
    pid = store.pair_id(names)
    existing = room["pairs"].get(pid) if n1.strip() else None
    taken = store.icons_taken(room, except_pair=pid)
    if existing and "sym" not in st.session_state:
        st.session_state["sym"] = existing["icon"]
        st.session_state["col"] = existing["color"]
    chosen = st.session_state.get("sym")
    color = st.session_state.get("col", icons.PALETTE[5][1])
    st.html('<div class="p-head">1 · Your colour</div>')
    _swatches(color)
    st.html('<div class="p-head">2 · Your symbol</div>')
    _tile_grid(icons.KEYS, chosen, taken, color, 5)
    if chosen:
        st.html(f'<div class="mean-line">You will appear as {icons.badge(chosen, color, " & ".join(n for n in names if n.strip()) or "…")}</div>')
    if existing:
        st.info("Welcome back. We found your earlier entry in this room.", icon=":material/history:")
    if st.button("Join", type="primary", icon=":material/login:", width="stretch", disabled=not (n1.strip() and chosen)):
        pair, err = store.join(room["code"], names, chosen, color)
        if err:
            st.html(f'<div class="err">{err}</div>')
        else:
            st.query_params["pair"] = pair["id"]
            st.rerun()
    return None


def current_pair(room: dict) -> dict | None:
    pid = st.query_params.get("pair")
    if pid and pid in room["pairs"]:
        return room["pairs"][pid]
    return None


def pair_header(room: dict, pair: dict, title: str):
    a, b = st.columns([3, 1], vertical_alignment="center")
    with a:
        st.html(f'<div class="p-head">{icons.svg(pair["icon"], pair["color"], 34)}{pair["label"]}'
                f'<span class="small" style="font-family:Barlow;font-weight:400;margin-left:.3rem">· room {room["code"]}</span></div>')
    with b:
        if st.button("Change symbol", key="chg", width="stretch"):
            st.session_state["sym"] = pair["icon"]
            st.session_state["col"] = pair["color"]
            st.session_state["n1"], st.session_state["n2"] = (pair["names"] + ["", ""])[:2]
            del st.query_params["pair"]
            st.rerun()
