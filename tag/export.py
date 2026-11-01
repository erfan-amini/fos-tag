"""Excel exports: the data, the summary numbers and the plot, in one workbook."""
from __future__ import annotations

import io
import time

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from tag import icons, plots
from tag.stats import fit_through_origin, overlap, summary

HEAD = PatternFill("solid", fgColor="0C2340")
HEAD_FONT = Font(bold=True, color="FFFFFF")


def _sheet(wb: Workbook, name: str, header: list[str], rows: list[list], widths: list[int] | None = None):
    ws = wb.create_sheet(name)
    ws.append(header)
    for c in range(1, len(header) + 1):
        cell = ws.cell(row=1, column=c)
        cell.fill, cell.font = HEAD, HEAD_FONT
        cell.alignment = Alignment(horizontal="center")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths or [], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    return ws


def _about(wb: Workbook, room: dict, activity: str, extra: list[tuple[str, str]] = ()):
    ws = wb.active
    ws.title = "About"
    ws["A1"], ws["B1"] = "Activity", activity
    ws["A2"], ws["B2"] = "Room", f"{room['code']}" + (f" ({room['title']})" if room.get("title") else "")
    ws["A3"], ws["B3"] = "Exported", time.strftime("%Y-%m-%d %H:%M")
    ws["A4"], ws["B4"] = "Pairs with data", sum(1 for p in room["pairs"].values() if p.get("data"))
    for i, (k, v) in enumerate(extra, start=5):
        ws[f"A{i}"], ws[f"B{i}"] = k, v
    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 40
    for r in range(1, 5 + len(extra)):
        ws[f"A{r}"].font = Font(bold=True)


def _plot_sheet(wb: Workbook, png: bytes, name: str = "Plot"):
    ws = wb.create_sheet(name)
    img = XLImage(io.BytesIO(png))
    img.width, img.height = img.width * 0.5, img.height * 0.5
    ws.add_image(img, "A1")


def _finish(wb: Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------- two-point threshold
def tpt_workbook(room: dict) -> bytes:
    wb = Workbook()
    _about(wb, room, "Two-Point Threshold")
    rows = plots.tpt_people(room)
    readings = []
    for pid in room["order"]:
        p = room["pairs"].get(pid)
        if not p or not p.get("data"):
            continue
        for person in p["data"].get("people", []):
            if not person.get("name"):
                continue
            for part in ("thumb", "forearm"):
                tr = (person.get(part, []) + [None, None, None])[:3]
                vals = [v for v in tr if v is not None]
                readings.append([p["label"], icons.LABEL[p["icon"]], icons.COLOR_NAME.get(p["color"], p["color"]),
                                 person["name"], part.capitalize(), *tr, round(sum(vals) / len(vals), 3) if vals else None])
    _sheet(wb, "Readings", ["Pair", "Symbol", "Colour", "Participant", "Part", "Trial 1 (mm)", "Trial 2 (mm)",
                            "Trial 3 (mm)", "Mean (mm)"], readings, [22, 11, 10, 16, 10, 12, 12, 12, 11])
    _sheet(wb, "Per person", ["Participant", "Pair", "Thumb mean (mm)", "Forearm mean (mm)"],
           [[r["name"], r["pair"], round(r["thumb"], 3), round(r["forearm"], 3)] for r in rows], [16, 22, 16, 18])
    th, fa = summary([r["thumb"] for r in rows]), summary([r["forearm"] for r in rows])
    ov = overlap(th, fa)
    summ = [[name, s["n"], *[round(s[k], 3) if s["n"] else None for k in ("mean", "sd", "se", "lo", "hi")]]
            for name, s in (("Thumb", th), ("Forearm", fa))]
    ws = _sheet(wb, "Summary", ["Part", "n", "Mean (mm)", "SD (mm)", "SE (mm)", "95% low (mean − 2 SE)",
                                "95% high (mean + 2 SE)"], summ, [12, 6, 12, 12, 12, 22, 22])
    ws["A5"] = "Do the two 95% intervals overlap?"
    ws["B5"] = "n/a" if ov is None else ("yes, difference not significant" if ov else "no, difference significant")
    ws["A5"].font = Font(bold=True)
    _plot_sheet(wb, plots.tpt_png(rows, f"Room {room['code']} · {room.get('title') or ''}".strip(" ·")))
    return _finish(wb)


# ---------------------------------------------------------------------------- ballooniverse
def balloon_workbook(room: dict) -> bytes:
    wb = Workbook()
    t = float(room["settings"].get("inflate_s", 10) or 10)
    _about(wb, room, "Ballooniverse", [("Inflation time (s)", t)])
    pts = plots.balloon_points(room)
    meas = []
    for pid in room["order"]:
        p = room["pairs"].get(pid)
        if not p or not p.get("data"):
            continue
        d = p["data"]
        for i, lab in enumerate(("Dot 1 (near)", "Dot 2 (middle)", "Dot 3 (far)")):
            a, b = d["init"][i], d["final"][i]
            ch = None if a is None or b is None else b - a
            meas.append([p["label"], icons.LABEL[p["icon"]], icons.COLOR_NAME.get(p["color"], p["color"]), lab, a, b, ch,
                         None if ch is None else round(ch / t, 4)])
        w = d.get("wavy", [None, None])
        meas.append([p["label"], icons.LABEL[p["icon"]], icons.COLOR_NAME.get(p["color"], p["color"]), "Wavy line (length)",
                     w[0], w[1], None if w[0] is None or w[1] is None else w[1] - w[0], None])
    _sheet(wb, "Measurements", ["Pair", "Symbol", "Colour", "Mark", "Initial (mm)", "Final (mm)", "Change (mm)",
                                "Velocity (mm/s)"], meas, [22, 11, 10, 18, 12, 12, 12, 14])
    f = fit_through_origin([r["final"] for r in pts], [r["v"] for r in pts])
    rows = [["Dots plotted", f["n"]], ["Trend through the origin: v = k × d, k (per second)", None if f["n"] < 2 else round(f["k"], 5)],
            ["R² of that line", None if f["n"] < 2 else round(f["r2"], 4)],
            ["Inflation time (s)", t]]
    _sheet(wb, "Summary", ["Quantity", "Value"], rows, [48, 14])
    _plot_sheet(wb, plots.balloon_png(pts, f"Room {room['code']} · {room.get('title') or ''}".strip(" ·"), t=t))
    return _finish(wb)
