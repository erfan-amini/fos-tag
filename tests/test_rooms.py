"""Store, statistics, plots and exports for the live activities."""
import io
import math
import time
from pathlib import Path

import pytest
from openpyxl import load_workbook

from tag import export, icons, plots
from tag.stats import dot_stack, fit_through_origin, nice_bin, overlap, summary
from tag.store import TTL, Store

FOREARM_41 = [1.67, 2.00, 3.00, 3.50, 5.67, 5.67, 10.33, 15.00, 16.67, 17.00, 18.00, 18.33, 19.00, 20.00, 20.67, 21.67,
              22.00, 22.67, 23.33, 23.33, 23.67, 24.33, 24.67, 25.33, 26.33, 27.67, 29.00, 29.33, 30.00, 31.33, 32.00,
              32.00, 32.00, 33.00, 33.67, 34.00, 38.67, 39.33, 52.00, 60.33, 69.00]


def fresh(tmp_path) -> Store:
    return Store(tmp_path / "rooms.json")


def test_summary_matches_the_activity_sheet():
    s = summary(FOREARM_41)
    assert s["n"] == 41
    assert abs(s["mean"] - 25.0) < 0.5          # the sheet's balance point is about 25 mm
    assert 12 < s["sd"] < 16
    assert abs(s["se"] - s["sd"] / math.sqrt(41)) < 1e-9
    assert s["lo"] < s["mean"] < s["hi"]


def test_overlap_and_nan():
    a, b = summary([3.5, 4.0, 4.5, 4.0]), summary(FOREARM_41)
    assert overlap(a, b) is False
    assert overlap(summary([1.0]), b) is None


def test_bins_and_stacking():
    assert nice_bin(0, 70) in (5, 10)
    assert nice_bin(2, 6) in (0.25, 0.5)
    pos = dot_stack([1.0, 1.2, 1.4, 2.6], 1.0)
    assert [k for _, k in pos] == [1, 2, 3, 1]


def test_fit_through_origin():
    f = fit_through_origin([10, 20, 40], [1, 2, 4])
    assert abs(f["k"] - 0.1) < 1e-9 and abs(f["r2"] - 1) < 1e-9
    assert math.isnan(fit_through_origin([], [])["k"])


def test_rooms_join_submit_and_unique_icons(tmp_path):
    st = fresh(tmp_path)
    room = st.create_room("tpt", {}, "Section 22")
    code = room["code"]
    assert len(code) == 4 and all(c in "ABCDEFGHJKMNPQRSTUVWXYZ" for c in code)
    p1, err = st.join(code, ["Ana", "Ben"], "star", "#0CA678")
    assert not err and p1["label"] == "Ana & Ben"
    p2, err = st.join(code, ["Coco", "Dev"], "star", "#F08C00")
    assert p2 is None and "taken" in err
    p2, err = st.join(code, ["Coco", "Dev"], "hexagon", "#F08C00")
    assert not err
    # same names come back to the same pair, and may keep their icon
    again, err = st.join(code, ["ben", " Ana "], "star", "#E03131")
    assert not err and again["id"] == p1["id"] and again["color"] == "#E03131"
    assert len(st.get(code)["pairs"]) == 2
    assert st.submit(code, p1["id"], {"people": [{"name": "Ana", "thumb": [3, 4, None], "forearm": [20, 22, 24]}]})
    assert st.get(code)["pairs"][p1["id"]]["data"]["people"][0]["thumb"] == [3, 4, None]
    # survives a restart from disk
    st2 = fresh(tmp_path)
    assert st2.get(code)["pairs"][p1["id"]]["label"] == "ben & Ana"      # the latest spelling wins
    assert st2.get(code.lower()) is not None
    st2.remove_pair(code, p2["id"])
    assert len(st2.get(code)["pairs"]) == 1 and st2.get(code)["order"] == [p1["id"]]


def test_old_rooms_are_swept(tmp_path):
    st = fresh(tmp_path)
    room = st.create_room("balloon")
    st.rooms[room["code"]]["updated"] = time.time() - TTL - 10
    st.sweep()
    assert st.get(room["code"]) is None


def test_bad_joins(tmp_path):
    st = fresh(tmp_path)
    assert st.join("ZZZZ", ["Ana"], "star", "#000")[1]
    room = st.create_room("tpt")
    assert st.join(room["code"], ["  "], "star", "#000")[1] == "Type at least one name."


def _tpt_room(st):
    room = st.create_room("tpt", {}, "Section 22")
    code = room["code"]
    vals = iter(FOREARM_41)
    for i, key in enumerate(icons.KEYS[:4]):
        p, _ = st.join(code, [f"A{i}", f"B{i}"], key, icons.PALETTE[i][1])
        people = [{"name": f"A{i}", "thumb": [3 + i * 0.2, 4, 3.5], "forearm": [next(vals), next(vals), next(vals)]},
                  {"name": f"B{i}", "thumb": [4.5, 5, None], "forearm": [next(vals), next(vals), next(vals)]}]
        st.submit(code, p["id"], {"people": people})
    return st.get(code)


def test_tpt_people_plot_and_export(tmp_path):
    room = _tpt_room(fresh(tmp_path))
    rows = plots.tpt_people(room)
    assert len(rows) == 8 and abs(rows[1]["thumb"] - 4.75) < 1e-9
    fig = plots.tpt_figure(rows)
    bars = [tr for tr in fig.data if tr.type == "bar"]
    assert [tr.name for tr in bars] == ["Thumb (mm)", "Forearm (mm)"]
    assert sum(bars[0].y) == 8 and sum(bars[1].y) == 8          # one count per student in each
    assert len([tr for tr in fig.data if tr.type == "scatter"]) == 2   # hover carriers for thumb and forearm
    assert len(fig.layout.images) == 16                                  # one symbol image per student per part
    fig2 = plots.tpt_figure(rows, show_stats=True)
    assert len(fig2.layout.shapes) == 4                           # two bands, two mean lines
    png = plots.tpt_png(rows, "test")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    wb = load_workbook(io.BytesIO(export.tpt_workbook(room)))
    assert wb.sheetnames == ["About", "Readings", "Per person", "Summary", "Plot"]
    ws = wb["Readings"]
    assert ws.max_row == 1 + 8 * 2
    assert ws["I2"].value == pytest.approx(3.5)        # mean of 3, 4, 3.5
    s = wb["Summary"]
    assert s["B2"].value == 8 and s["B3"].value == 8
    assert len(wb["Plot"]._images) == 1


def test_balloon_points_and_export(tmp_path):
    st = fresh(tmp_path)
    room = st.create_room("balloon", {"inflate_s": 10}, "Section 24")
    code = room["code"]
    p, _ = st.join(code, ["Eve"], "plus", "#1C7ED6")
    st.submit(code, p["id"], {"init": [20, 60, 120], "final": [35, 95, 185], "wavy": [30, 48]})
    rows = plots.balloon_points(st.get(code))
    assert [r["v"] for r in rows] == [1.5, 3.5, 6.5]
    wb = load_workbook(io.BytesIO(export.balloon_workbook(st.get(code))))
    ws = wb["Measurements"]
    assert ws.max_row == 5 and ws["H2"].value == 1.5 and ws["D5"].value == "Wavy line (length)"
    assert wb["Summary"]["B3"].value is not None
    assert len(wb["Plot"]._images) == 1
    fig = plots.balloon_figure(rows, trend=True)
    assert any(t.name == "trend" for t in fig.data)


def test_symbols_are_consistent():
    assert len(icons.KEYS) == 15 and len(icons.FUNNY) == 8
    assert len(icons.PALETTE) == 11
    for k in icons.KEYS:
        assert icons.svg(k, "#000").startswith("<img")
        path = icons.mpl_path(k)
        assert len(path.vertices) > 3 and path.get_extents().width > 60     # drawn and roughly fills the box
    assert icons.path_d("no-such-symbol") == icons.path_d("circle")           # old rooms never crash
