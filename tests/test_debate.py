"""The debate rules: roles, the clock, the panel's two votes, reactions and the count."""
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
    assert [x["key"] for x in segs][-3:] == ["close", "vote", "result"]
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


def test_panel_votes_before_and_after_and_is_locked_in_between(tmp_path):
    _, room = make_room(tmp_path)                         # panel on resolution 1: Eli, Fay (T3), Gus, Hana, Ivy (T4)
    L.start_resolution(room, 0)
    assert not L.set_stance(room, "ana", "for")          # a debater cannot vote
    assert not L.set_stance(room, "eli", "und")          # there is no "Not sure"
    for pid, side in [("eli", "for"), ("fay", "against"), ("gus", "against"), ("hana", "for"), ("hana", "against")]:
        assert L.set_stance(room, pid, side)              # a second tap in the same step replaces the first
    t = L.tally(room)
    assert (t["n"], t["picked"], t["voted"], t["before"]) == (5, 4, 0, {"for": 1, "against": 3})
    for seg in range(1, L.SEG_VOTE):                      # every speech: locked
        L.go_seg(room, seg)
        assert not L.set_stance(room, "eli", "against") and not L.set_stance(room, "ivy", "for")
    L.go_seg(room, L.SEG_VOTE)
    assert L.timer_running(room["debate"]["timer"])       # the vote clock starts by itself
    for pid, side in [("fay", "for"), ("gus", "for"), ("hana", "against"), ("ivy", "for")]:
        assert L.set_stance(room, pid, side)              # Eli does not vote again: his first vote stands
    L.go_seg(room, L.SEG_RESULT)                          # the host counts: closed
    assert not L.set_stance(room, "eli", "against")
    t = L.tally(room)
    assert t["before"] == {"for": 1, "against": 3}
    assert t["after"] == {"for": 4, "against": 1}         # Ivy voted only at the end
    assert t["won"] == {"for": 2, "against": 0} and t["moved"] == 2
    assert (t["winner"], t["how"], t["voted"]) == ("for", "swing", 4)
    assert t["swing"] == {"for": 3, "against": -2}
    L.go_seg(room, L.SEG_VOTE)                            # back one step opens the final vote again
    assert L.set_stance(room, "eli", "against")
    assert room["debate"]["votes"]["0"]["eli"] == {"pre": "for", "post": "against"}


def test_the_side_that_wins_over_more_of_the_panel_wins(tmp_path):
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)

    def run(pre, post):
        L.reset_resolution(room, 0)
        L.go_seg(room, 0)
        for pid, side in pre.items():
            L.set_stance(room, pid, side)
        L.go_seg(room, L.SEG_VOTE)
        for pid, side in post.items():
            L.set_stance(room, pid, side)
        L.go_seg(room, L.SEG_RESULT)
        return L.tally(room)

    every = ["eli", "fay", "gus", "hana", "ivy"]
    # For still has more at the end, but Against won someone over: Against wins
    t = run(dict.fromkeys(every[:4], "for") | {"ivy": "against"}, {"eli": "against"})
    assert t["after"] == {"for": 3, "against": 2} and (t["winner"], t["how"]) == ("against", "swing")
    # nobody switched: the count at the end decides
    t = run({"eli": "for", "fay": "for", "gus": "against"}, {"eli": "for", "fay": "for", "gus": "against"})
    assert (t["winner"], t["how"], t["moved"]) == ("for", "count", 0)
    # one switch each way: the count decides
    t = run({"eli": "for", "fay": "against", "gus": "for"}, {"eli": "against", "fay": "for"})
    assert t["won"] == {"for": 1, "against": 1} and (t["winner"], t["how"]) == ("for", "count")
    # level before and after
    t = run({"eli": "for", "fay": "against"}, {})
    assert (t["winner"], t["how"]) == (None, "tie")
    L.reset_resolution(room, 0)
    assert L.tally(room)["picked"] == 0


def test_a_room_with_votes_in_an_older_format_still_counts(tmp_path):
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)
    room["debate"]["votes"]["0"] = {"eli": {"pre": "und", "now": "for", "moves": 1}, "fay": {"pre": "for", "now": "for"}}
    t = L.tally(room)
    assert t["before"] == {"for": 1, "against": 0} and t["picked"] == 1


def test_reactions_only_from_the_panel_during_a_speech(tmp_path):
    _, room = make_room(tmp_path)
    L.start_resolution(room, 0)
    assert not L.react(room, "eli", "agree", 10)           # nobody is speaking during preparation
    L.go_seg(room, 1)                                     # opening, for
    assert not L.react(room, "cleo", "agree", 10)          # the other debating team cannot react
    assert L.react(room, "eli", "agree", 10)
    assert not L.react(room, "eli", "fire", 10.5)         # too fast
    assert L.react(room, "eli", "fire", 12) and L.react(room, "gus", "agree", 12)
    assert not L.react(room, "gus", "nope", 20)
    L.go_seg(room, 2)                                     # opening, against
    assert L.react(room, "fay", "hmm", 30)
    t = L.tally(room)
    assert t["reacts"]["for"] == {"agree": 2, "fire": 1} and t["reacts"]["against"] == {"hmm": 1}
    assert [f[1] for f in L.recent_feed(room, 31)] == ["hmm"]
    for i in range(200):
        L.react(room, "fay", "agree", 100 + 2 * i)
    assert len(room["debate"]["feed"]) == L.FEED_KEEP


def test_room_survives_the_store(tmp_path):
    store, room = make_room(tmp_path)
    code = room["code"]
    store.update(code, lambda r: L.start_resolution(r, 0))
    store.update(code, lambda r: L.set_stance(r, "eli", "for"))
    store.update(code, lambda r: L.go_seg(r, 1))
    store.update(code, lambda r: L.react(r, "eli", "agree"), save=False)
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
    assert room["debate"]["votes"]["0"]["eli"]["pre"] == "for"     # votes are kept
    L.timer_start(room["debate"]["timer"], 0)
    new["times"]["prep"] = 60
    L.apply_settings(room, new)
    assert room["debate"]["timer"]["dur"] == 180                   # a started clock keeps its time
    L.go_seg(room, 1)
    assert L.timer_left(room["debate"]["timer"]) == 90
