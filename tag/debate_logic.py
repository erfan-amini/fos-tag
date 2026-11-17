"""Debate: the rules, with no Streamlit in sight so they can be tested.

A room has teams. Each resolution names one team that argues for it and one that argues
against it; everybody else is the panel. The panel picks a side before the opening, can
react to each speech and change sides while it listens, and gives a final vote. Every
function here changes the room dict in place and is meant to run inside Store.update().
"""
from __future__ import annotations

import re
import time

SIDES = ("for", "against")
STANCES = ("for", "und", "against")
STANCE_LABEL = {"for": "For", "und": "Not sure", "against": "Against"}

# key, emoji, what it means. Erfan's pick: two for a good argument, two for being moved, two for doubt.
EMOJI = [
    ("agree", "👍", "Agree"),
    ("fire", "🔥", "Great rebuttal"),
    ("wow", "😮", "Surprising"),
    ("turn", "🔄", "Changing my mind"),
    ("hmm", "🤔", "Not convinced"),
    ("really", "🤨", "Really?"),
]
EMOJI_CHAR = {k: e for k, e, _ in EMOJI}
REACT_COOLDOWN = 1.2          # seconds between two reactions from one phone
FEED_KEEP = 60                # reactions kept for the floating animation

TEAM_COLORS = ["#1C7ED6", "#F08C00", "#0CA678", "#7048E8", "#E64980", "#8B5A2B"]
FOR_COLOR = "#1E7B46"
AGAINST_COLOR = "#B4282C"

DEFAULT_TIMES = {"prep": 300, "open": 120, "rebut": 60, "close": 60, "vote": 30}

ML2 = {
    "label": "Molecules and Life 2: cancer, money and ethics",
    "resolutions": [
        {"title": "You set the cancer budget", "scene": "",
         "text": "Governments should stop paying for cancer drugs that add less than a year of life, and fund "
                 "prevention and screening instead.",
         "for": 1, "against": 2,
         "hint_for": "Cervical cancer: what a vaccine and screening did. How many people prevention reaches, and the "
                     "cost per person.",
         "hint_against": "The patient who is sick today cannot wait. First drugs lead to better ones: KRAS took forty "
                         "years, and now the door is open.",
         "img_for": "debate_prevention.jpg", "img_against": "debate_drug.jpg",
         "cap_for": "Prevention and screening", "cap_against": "New drugs"},
        {"title": "Is it fair to randomize?", "scene": "",
         "text": "Once early results suggest a new drug works, it is unethical to randomize terminally ill "
                 "patients to standard treatment.",
         "for": 3, "against": 4,
         "hint_for": "These patients have little time. They joined hoping for the new drug, and half did not get it.",
         "hint_against": "Early results can be wrong. Without a comparison group we may never know if the drug works. "
                         "First question: was it a fair trial?",
         "img_for": "debate_patient.jpg", "img_against": "debate_trial.jpg",
         "cap_for": "The patient cannot wait", "cap_against": "The fair comparison"},
    ],
    "debrief": ["Which argument stayed with you?",
                "Did anyone change their mind? What moved you?",
                "A result can be statistically significant. Is that the same as meaningful?"],
}

BLANK_DEBRIEF = ["Which argument stayed with you?", "Did anyone change their mind? What moved you?"]


def blank_resolution(i: int, teams: int) -> dict:
    f = (2 * i) % teams + 1
    a = (2 * i + 1) % teams + 1
    return {"title": "", "scene": "", "text": "", "for": f, "against": a, "hint_for": "", "hint_against": "",
            "img_for": "", "img_against": "", "cap_for": "", "cap_against": ""}


def default_settings(preset: str = "ml2", teams: int = 4, n_res: int = 2) -> dict:
    src = ML2["resolutions"] if preset == "ml2" else []
    res = [dict(src[i]) if i < len(src) else blank_resolution(i, teams) for i in range(n_res)]
    return {"teams": teams, "times": dict(DEFAULT_TIMES), "resolutions": res,
            "debrief": list(ML2["debrief"] if preset == "ml2" else BLANK_DEBRIEF)}


# ---------------------------------------------------------------------------- segments
def segments(settings: dict) -> list[dict]:
    t = {**DEFAULT_TIMES, **(settings.get("times") or {})}
    return [
        {"key": "prep", "label": "Prepare", "side": None, "dur": t["prep"]},
        {"key": "open", "label": "Opening", "side": "for", "dur": t["open"]},
        {"key": "open", "label": "Opening", "side": "against", "dur": t["open"]},
        {"key": "rebut", "label": "Rebuttal", "side": "for", "dur": t["rebut"]},
        {"key": "rebut", "label": "Rebuttal", "side": "against", "dur": t["rebut"]},
        {"key": "close", "label": "Closing", "side": "for", "dur": t["close"]},
        {"key": "close", "label": "Closing", "side": "against", "dur": t["close"]},
        {"key": "vote", "label": "Final vote", "side": None, "dur": t["vote"]},
        {"key": "result", "label": "Result", "side": None, "dur": 0},
    ]


N_SEGS = 9
SEG_VOTE, SEG_RESULT = 7, 8


# ---------------------------------------------------------------------------- timer
def new_timer(dur: float, v: int = 0) -> dict:
    return {"dur": float(dur), "left": float(dur), "run_at": None, "v": v}


def timer_left(timer: dict, now: float | None = None) -> float:
    if timer.get("run_at") is None:
        return timer["left"]
    return timer["left"] - ((now if now is not None else time.time()) - timer["run_at"])


def timer_running(timer: dict) -> bool:
    return timer.get("run_at") is not None


def timer_state(timer: dict, now: float | None = None) -> str:
    """idle (full, not started), running, paused, over."""
    left = timer_left(timer, now)
    if timer["dur"] <= 0:
        return "none"
    if left <= 0:
        return "over"
    if timer_running(timer):
        return "running"
    return "idle" if abs(timer["left"] - timer["dur"]) < 1e-6 else "paused"


def timer_start(timer: dict, now: float | None = None):
    if timer.get("run_at") is None and timer["left"] > 0:
        timer["run_at"] = now if now is not None else time.time()
        timer["v"] += 1


def timer_pause(timer: dict, now: float | None = None):
    if timer.get("run_at") is not None:
        timer["left"] = max(0.0, timer_left(timer, now))
        timer["run_at"] = None
        timer["v"] += 1


def timer_reset(timer: dict):
    timer["left"], timer["run_at"] = timer["dur"], None
    timer["v"] += 1


def timer_add(timer: dict, seconds: float, now: float | None = None):
    """Add time. An expired clock comes back with just the added time, still running."""
    left = timer_left(timer, now)
    running = timer_running(timer)
    timer["left"] = max(0.0, left) + seconds
    timer["run_at"] = (now if now is not None else time.time()) if running else None
    timer["v"] += 1


# ---------------------------------------------------------------------------- room state
def init_room(room: dict):
    room["people"] = {}
    room["debate"] = {"stage": "lobby", "r": 0, "seg": 0, "timer": new_timer(0),
                      "votes": {}, "reacts": {}, "feed": [], "fid": 0}


def apply_settings(room: dict, new: dict):
    """Edit texts and times while the room is open. Teams and the number of resolutions stay as they are;
    an idle clock takes its new length at once, a started one keeps running."""
    s = room["settings"]
    s["times"] = {**DEFAULT_TIMES, **{k: int(v) for k, v in (new.get("times") or {}).items() if k in DEFAULT_TIMES}}
    for old, res in zip(s["resolutions"], new.get("resolutions") or []):
        for k in ("title", "scene", "text", "hint_for", "hint_against"):
            old[k] = str(res.get(k, old.get(k, ""))).strip()
        f, a = int(res.get("for", old["for"])), int(res.get("against", old["against"]))
        if f != a and 1 <= f <= s["teams"] and 1 <= a <= s["teams"]:
            old["for"], old["against"] = f, a
    s["debrief"] = [q for q in new.get("debrief", s.get("debrief", [])) if q.strip()]
    d = room["debate"]
    if d["stage"] == "run" and timer_state(d["timer"]) in ("idle", "none"):
        d["timer"] = new_timer(segments(s)[d["seg"]]["dur"], d["timer"]["v"] + 1)


def team_name(t: int) -> str:
    return f"Team {t}"


def team_color(t: int) -> str:
    return TEAM_COLORS[(t - 1) % len(TEAM_COLORS)]


def person_id(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def join(room: dict, name: str, team: int) -> tuple[str | None, str]:
    """Add a person or move them to another team. Same name means same person."""
    name = " ".join(name.split())[:24]
    pid = person_id(name)
    if not pid:
        return None, "Type your first name."
    if not 1 <= int(team) <= int(room["settings"]["teams"]):
        return None, "Pick a team."
    p = room["people"].get(pid)
    if p is None:
        room["people"][pid] = {"id": pid, "name": name, "team": int(team), "joined": time.time()}
    else:
        p.update({"name": name, "team": int(team)})
    return pid, ""


def remove_person(room: dict, pid: str):
    room["people"].pop(pid, None)
    for votes in room["debate"]["votes"].values():
        votes.pop(pid, None)


def members(room: dict, team: int) -> list[dict]:
    return sorted((p for p in room["people"].values() if p["team"] == team), key=lambda p: p["joined"])


def resolution(room: dict, r: int | None = None) -> dict:
    d = room["debate"]
    res = room["settings"]["resolutions"]
    return res[min(d["r"] if r is None else r, len(res) - 1)]


def role(room: dict, team: int, r: int | None = None) -> str:
    """'for', 'against' or 'panel' for this team on a resolution."""
    res = resolution(room, r)
    if team == res["for"]:
        return "for"
    if team == res["against"]:
        return "against"
    return "panel"


def panel(room: dict, r: int | None = None) -> list[dict]:
    return [p for p in room["people"].values() if role(room, p["team"], r) == "panel"]


def panel_teams(room: dict, r: int | None = None) -> list[int]:
    return [t for t in range(1, int(room["settings"]["teams"]) + 1) if role(room, t, r) == "panel"]


def _votes(room: dict, r: int) -> dict:
    return room["debate"]["votes"].setdefault(str(r), {})


def _reacts(room: dict, r: int) -> dict:
    return room["debate"]["reacts"].setdefault(str(r), {"for": {}, "against": {}})


def current_seg(room: dict) -> dict:
    return segments(room["settings"])[room["debate"]["seg"]]


# ---------------------------------------------------------------------------- moving through the debate
def start_resolution(room: dict, r: int):
    d = room["debate"]
    d.update({"stage": "run", "r": r, "seg": 0})
    d["timer"] = new_timer(segments(room["settings"])[0]["dur"], d["timer"]["v"] + 1)
    _votes(room, r)
    _reacts(room, r)


def _snapshot(room: dict):
    """Freeze where the panel stood before the first speech."""
    d = room["debate"]
    votes = _votes(room, d["r"])
    for p in panel(room):
        v = votes.setdefault(p["id"], {"pre": None, "now": None, "moves": 0, "final": False})
        v["pre"] = v["now"] or "und"
        v["now"] = v["now"] or "und"
        v["moves"] = 0
    d["snap"] = {**d.get("snap", {}), str(d["r"]): True}


def go_seg(room: dict, seg: int, now: float | None = None):
    d = room["debate"]
    seg = max(0, min(N_SEGS - 1, seg))
    if d["seg"] == 0 and seg > 0:
        _snapshot(room)
    if seg == 0:
        d.get("snap", {}).pop(str(d["r"]), None)
    d["seg"] = seg
    d["timer"] = new_timer(segments(room["settings"])[seg]["dur"], d["timer"]["v"] + 1)
    if seg == SEG_VOTE:
        timer_start(d["timer"], now)          # the vote clock starts by itself


def finish(room: dict):
    room["debate"]["stage"] = "done"


def back_to_lobby(room: dict):
    room["debate"]["stage"] = "lobby"


def reset_resolution(room: dict, r: int):
    d = room["debate"]
    d["votes"][str(r)] = {}
    d["reacts"][str(r)] = {"for": {}, "against": {}}
    d.get("snap", {}).pop(str(r), None)


def snapshot_taken(room: dict, r: int | None = None) -> bool:
    d = room["debate"]
    return bool(d.get("snap", {}).get(str(d["r"] if r is None else r)))


# ---------------------------------------------------------------------------- the panel acts
def set_stance(room: dict, pid: str, stance: str, final: bool = False) -> bool:
    d = room["debate"]
    p = room["people"].get(pid)
    if p is None or stance not in STANCES or d["stage"] != "run" or role(room, p["team"]) != "panel":
        return False
    if d["seg"] >= SEG_RESULT:
        return False
    v = _votes(room, d["r"]).setdefault(pid, {"pre": None, "now": None, "moves": 0, "final": False})
    if snapshot_taken(room):
        if v["pre"] is None:                   # joined after the opening began
            v["pre"] = "und"
        if v["now"] != stance:
            v["moves"] += 1
    v["now"] = stance
    if final:
        v["final"] = True
    return True


def react(room: dict, pid: str, emoji: str, now: float | None = None) -> bool:
    """A reaction to the team that is speaking. Panel only, and only during a speech."""
    now = now if now is not None else time.time()
    d = room["debate"]
    p = room["people"].get(pid)
    seg = current_seg(room)
    if p is None or emoji not in EMOJI_CHAR or d["stage"] != "run" or seg["side"] is None:
        return False
    if role(room, p["team"]) != "panel":
        return False
    if now - p.get("last_react", 0) < REACT_COOLDOWN:
        return False
    p["last_react"] = now
    side = _reacts(room, d["r"])[seg["side"]]
    side[emoji] = side.get(emoji, 0) + 1
    d["fid"] += 1
    d["feed"].append([round(now, 2), emoji, seg["side"], d["fid"]])
    del d["feed"][:-FEED_KEEP]
    return True


# ---------------------------------------------------------------------------- counting
def tally(room: dict, r: int | None = None) -> dict:
    """Where the panel stood before and stands now, and who won."""
    d = room["debate"]
    r = d["r"] if r is None else r
    votes = d["votes"].get(str(r), {})
    people = panel(room, r)
    snap = snapshot_taken(room, r)
    before = {s: 0 for s in STANCES}
    after = {s: 0 for s in STANCES}
    picked = moved = final = 0
    for p in people:
        v = votes.get(p["id"]) or {}
        now_ = v.get("now")
        if now_:
            picked += 1
        pre = (v.get("pre") or "und") if snap else (now_ or "und")
        cur = now_ or "und"
        before[pre] += 1
        after[cur] += 1
        if snap and pre != cur:
            moved += 1
        if v.get("final"):
            final += 1
    swing = {s: after[s] - before[s] for s in SIDES}
    if after["for"] != after["against"]:
        winner = "for" if after["for"] > after["against"] else "against"
        how = "votes"
    elif swing["for"] != swing["against"]:
        winner = "for" if swing["for"] > swing["against"] else "against"
        how = "swing"
    else:
        winner, how = None, "tie"
    reacts = d["reacts"].get(str(r), {"for": {}, "against": {}})
    return {"n": len(people), "picked": picked, "before": before, "after": after, "moved": moved, "final": final,
            "swing": swing, "winner": winner, "how": how, "reacts": reacts, "snap": snap}


def recent_feed(room: dict, now: float | None = None, window: float = 3.6) -> list[list]:
    now = now if now is not None else time.time()
    return [f for f in room["debate"]["feed"] if 0 <= now - f[0] < window]
