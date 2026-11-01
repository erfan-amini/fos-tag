"""Shared, short-lived storage for the live activities.

One Store object lives in the server process (through st.cache_resource), so every
browser that opens the app sees the same rooms. Every change is also written to
data/rooms.json, so a restart of the Python process (not a redeploy) keeps the rooms.
Rooms older than TTL are dropped.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
from pathlib import Path

TTL = 24 * 3600                      # a room lives this long after its last change
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ"   # no I, L or O: they read badly on a projector
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "rooms.json"


def now() -> float:
    return time.time()


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path or DATA_FILE
        self.lock = threading.RLock()
        self.rooms: dict[str, dict] = {}
        self._load()

    # ---------------------------------------------------------------- disk
    def _load(self):
        try:
            if self.path.exists():
                self.rooms = json.loads(self.path.read_text())
        except Exception:
            self.rooms = {}
        self.sweep()

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.rooms))
            os.replace(tmp, self.path)
        except Exception:
            pass                     # storage is best effort; the in-memory copy still works

    def sweep(self):
        cutoff = now() - TTL
        with self.lock:
            old = [c for c, r in self.rooms.items() if r.get("updated", 0) < cutoff]
            for c in old:
                del self.rooms[c]
            if old:
                self._save()

    # ---------------------------------------------------------------- rooms
    def new_code(self) -> str:
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
            if code not in self.rooms:
                return code

    def create_room(self, kind: str, settings: dict | None = None, title: str = "") -> dict:
        with self.lock:
            code = self.new_code()
            room = {"code": code, "kind": kind, "title": title, "created": now(), "updated": now(),
                    "settings": settings or {}, "pairs": {}, "order": []}
            self.rooms[code] = room
            self._save()
            return room

    def get(self, code: str | None) -> dict | None:
        if not code:
            return None
        with self.lock:
            return self.rooms.get(code.upper())

    def rooms_of(self, kind: str) -> list[dict]:
        with self.lock:
            rs = [r for r in self.rooms.values() if r["kind"] == kind]
        return sorted(rs, key=lambda r: -r["updated"])

    def update(self, code: str, fn) -> dict | None:
        """Run fn(room) under the lock, stamp the room and save. Returns the room."""
        with self.lock:
            room = self.rooms.get(code.upper())
            if room is None:
                return None
            fn(room)
            room["updated"] = now()
            self._save()
            return room

    def delete_room(self, code: str):
        with self.lock:
            self.rooms.pop(code.upper(), None)
            self._save()

    # ---------------------------------------------------------------- pairs
    @staticmethod
    def pair_id(names: list[str]) -> str:
        key = "|".join(sorted(n.strip().lower() for n in names if n.strip()))
        return key or "anonymous"

    def icons_taken(self, room: dict, except_pair: str | None = None) -> dict[str, str]:
        """icon key -> pair label, for icons already chosen in this room."""
        return {p["icon"]: p["label"] for pid, p in room["pairs"].items()
                if pid != except_pair and p.get("icon")}

    def join(self, code: str, names: list[str], icon: str, color: str) -> tuple[dict | None, str]:
        """Create or update a pair. Returns (pair, error)."""
        names = [n.strip() for n in names if n.strip()]
        if not names:
            return None, "Type at least one name."
        pid = self.pair_id(names)
        err = ""
        out = {}

        def fn(room):
            nonlocal err
            taken = self.icons_taken(room, except_pair=pid)
            if icon in taken:
                err = f"That symbol is taken by {taken[icon]}. Pick another one."
                return
            p = room["pairs"].get(pid)
            if p is None:
                p = {"id": pid, "names": names, "label": " & ".join(names), "icon": icon, "color": color,
                     "joined": now(), "updated": now(), "data": None}
                room["pairs"][pid] = p
                room["order"].append(pid)
            else:
                p.update({"names": names, "label": " & ".join(names), "icon": icon, "color": color, "updated": now()})
            out.update(p)

        room = self.update(code, fn)
        if room is None:
            return None, "That room does not exist, or it has expired."
        if err:
            return None, err
        return out, ""

    def submit(self, code: str, pid: str, data: dict) -> bool:
        def fn(room):
            p = room["pairs"].get(pid)
            if p is not None:
                p["data"] = data
                p["updated"] = now()
        return self.update(code, fn) is not None

    def remove_pair(self, code: str, pid: str):
        def fn(room):
            room["pairs"].pop(pid, None)
            room["order"] = [x for x in room["order"] if x != pid]
        self.update(code, fn)


_store: Store | None = None
_store_lock = threading.Lock()


def get_store() -> Store:
    """The one store for this server. Works with or without Streamlit."""
    global _store
    try:
        import streamlit as st

        @st.cache_resource(show_spinner=False)
        def _cached() -> Store:
            return Store()
        return _cached()
    except Exception:
        with _store_lock:
            if _store is None:
                _store = Store()
            return _store
