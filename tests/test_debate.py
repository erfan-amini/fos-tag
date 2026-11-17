"""The debate rules: roles, the clock, the panel's sides, reactions and the count."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tag import debate_logic as L
from tag.store import Store


def make_room(tmp_path, people=True):
    store = Store(tmp_path / "rooms.json")
    room = store.create_room("debate", L.default_settings("ml2"), "Section 22")
    L.init_room(room)
    if people:
        for name, team in [("Ana", 1), ("Ben", 1), ("Cleo", 2), ("Dev", 2), ("Eli", 3), ("Fay", 3), ("Gus", 4),
                           ("Hana", 4), ("Ivy", 4)]:
            L.join(room, name, team)
    return store, room


def test_preset_follows_the_slides():
    s = L.default_settings("ml2")
    assert s["teams"] == 4 and len(s["resolutions"]) == 2
    r1, r2 = s["resolutions"]
    assert (r1["for"], r1["against"], r2["for"], r2["against"]) == (1, 2, 3, 4)
    segs = L.segments(s)
    assert [x["dur"] for x in segs] == [300, 120, 120, 60, 60, 60, 60, 30, 0]
    assert [x["side"] for x in segs[1:7]] == ["for", "against"] * 3
    blank = L.default_settings("blank", teams=3, n_res=3)
    assert all(r["for"] != r["against"] for r in blank["resolutions"])


def test_join_roles_and_rejoin(tmp_path):
    _, room = make_room(tmp_path)
    assert L.join(room, "  ", 1) == (None, "Type your first name.")
    assert L.join(room, "Zed", 9)[0] is None
    pid, _ = L.join(room, "ana", 2)                    # same name: same person, moved to team 2
    assert pid == "ana" and room["people"]["ana"]["team"] == 2 and len(room["people"]) == 9
    L.join(room, "Ana", 1)
    L.start_resolution(room, 0)
    assert [L.role(room, t) for t in (1, 2, 3, 4)] == ["for", "against", "panel", "panel"]
    assert L.panel_teams(room) == [3, 4] and len(L.panel(room)) == 5
    L.start_resolution(room, 1)
    assert [L.role(room, t) for t in (1, 2, 3, 4)] == ["panel", "panel", "for", "against"]


def test_clock():
    t = L.new_timer(120)
    assert L.timer_state(t, 0) == "idle" and L.timer_left(t, 50) == 120
    L.timer_start(t, 100)
    assert L.timer_state(t, 130) == "running" and L.timer_left(t, 130) == 90
    L.timer_pause(t, 130)
    assert L.timer_state(t, 500) == "paused" and L.timer_left(t, 500) == 90
    L.timer_start(t, 200)
    assert L.timer_state(t, 291) == "over"
    L.timer_add(t, 30, 300)                              # expired and still running: comes back with 30 s
    assert L.timer_state(t, 310) == "running" and round(L.timer_left(t, 310)) == 20
    L.timer_reset(t)
    assert L.timer_state(t, 999) == "idle"
    assert L.timer_state(L.new_timer(0)) == "none"
    assert len({L.new_timer(5)["v"], t["v"]}) == 2      # every change gives the clock a new key


def test_panel_picks_changes_and_votes(tmp_path):
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)
    assert not L.set_stance(room, "ana", "for")          # a debater cannot vote
    assert L.set_stance(room, "eli", "for") and L.set_stance(room, "fay", "against") and L.set_stance(room, "gus", "against")
    t = L.tally(room)
    assert (t["n"], t["picked"], t["snap"]) == (5, 3, False)
    L.go_seg(room, 1)                                     # the opening starts: the starting split is frozen
    t = L.tally(room)
    assert t["before"] == {"for": 1, "und": 2, "against": 2} and t["moved"] == 0
    L.set_stance(room, "hana", "for")                     # was not sure
    L.set_stance(room, "fay", "for")                      # changed sides
    L.set_stance(room, "fay", "for")                      # tapping the same side again is not a move
    assert room["debate"]["votes"]["0"]["fay"]["moves"] == 1
    L.go_seg(room, L.SEG_VOTE)
    assert L.timer_running(room["debate"]["timer"])       # the vote clock starts by itself
    L.set_stance(room, "ivy", "against", final=True)
    L.go_seg(room, L.SEG_RESULT)
    assert not L.set_stance(room, "eli", "against")       # closed
    t = L.tally(room)
    assert t["after"] == {"for": 3, "und": 0, "against": 2}
    assert t["before"] == {"for": 1, "und": 2, "against": 2}
    assert (t["winner"], t["how"], t["moved"], t["final"]) == ("for", "votes", 3, 1)
    assert t["swing"] == {"for": 2, "against": 0}


def test_tie_goes_to_the_side_that_moved_more(tmp_path):
    _, room = make_room(tmp_path)
    L.join(room, "Jo", 3)
    L.start_resolution(room, 0)
    for pid, s in [("eli", "for"), ("fay", "for"), ("gus", "for"), ("hana", "against")]:
        L.set_stance(room, pid, s)
    L.go_seg(room, 1)
    for pid, s in [("ivy", "against"), ("jo", "against")]:
        L.set_stance(room, pid, s)
    t = L.tally(room)
    assert t["after"]["for"] == t["after"]["against"] == 3
    assert (t["winner"], t["how"]) == ("against", "swing")
    L.reset_resolution(room, 0)
    assert L.tally(room)["winner"] is None


def test_reactions_only_from_the_panel_during_a_speech(tmp_path):
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)
    assert not L.react(room, "eli", "clap", 10)           # nobody is speaking during preparation
    L.go_seg(room, 1)                                     # opening, for
    assert not L.react(room, "cleo", "clap", 10)          # the other debating team cannot react
    assert L.react(room, "eli", "clap", 10)
    assert not L.react(room, "eli", "data", 10.5)         # too fast
    assert L.react(room, "eli", "data", 12) and L.react(room, "gus", "clap", 12)
    assert not L.react(room, "gus", "nope", 20)
    L.go_seg(room, 2)                                     # opening, against
    assert L.react(room, "fay", "hmm", 30)
    t = L.tally(room)
    assert t["reacts"]["for"] == {"clap": 2, "data": 1} and t["reacts"]["against"] == {"hmm": 1}
    assert [f[1] for f in L.recent_feed(room, 31)] == ["hmm"]
    for i in range(200):
        L.react(room, "fay", "clap", 100 + 2 * i)
    assert len(room["debate"]["feed"]) == L.FEED_KEEP


def test_room_survives_the_store(tmp_path):
    store, room = make_room(tmp_path)
    code = room["code"]
    store.update(code, lambda r: L.start_resolution(r, 0))
    store.update(code, lambda r: L.set_stance(r, "eli", "for"))
    store.update(code, lambda r: L.go_seg(r, 1))
    store.update(code, lambda r: L.react(r, "eli", "clap"), save=False)
    again = Store(tmp_path / "rooms.json").get(code)      # what a restarted server would read
    assert again["debate"]["seg"] == 1 and again["debate"]["votes"]["0"]["eli"]["pre"] == "for"
    L.remove_person(room, "eli")
    assert "eli" not in room["people"] and "eli" not in room["debate"]["votes"]["0"]


def test_texts_and_times_can_change_while_the_room_is_open(tmp_path):
    import copy
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)
    L.set_stance(room, "eli", "for")
    new = copy.deepcopy(room["settings"])
    new["times"].update({"prep": 180, "open": 90})
    new["resolutions"][0]["text"] = "  A new wording.  "
    new["resolutions"][1].update({"for": 4, "against": 4})        # not allowed: one team on both sides
    L.apply_settings(room, new)
    assert room["settings"]["resolutions"][0]["text"] == "A new wording."
    assert (room["settings"]["resolutions"][1]["for"], room["settings"]["resolutions"][1]["against"]) == (3, 4)
    assert L.timer_left(room["debate"]["timer"]) == 180            # the idle clock took the new length
    assert room["debate"]["votes"]["0"]["eli"]["now"] == "for"     # votes are kept
    L.timer_start(room["debate"]["timer"], 0)
    new["times"]["prep"] = 60
    L.apply_settings(room, new)
    assert room["debate"]["timer"]["dur"] == 180                   # a started clock keeps its time
    L.go_seg(room, 1)
    assert L.timer_left(room["debate"]["timer"]) == 90
