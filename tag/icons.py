"""The fifteen pair symbols and the colour palette.

Seven plain shapes and eight funny ones. Each symbol is one SVG path drawn in a 100 x 100
box. The same path is used three ways: as an <img> in the picker and the chips, as an image
placed on the Plotly boards, and as a Matplotlib marker in the Excel export, so a pair looks
the same everywhere.
"""
from __future__ import annotations

import base64
import math
import re
from functools import lru_cache

# key, label
SYMBOLS = [
    ("circle", "Circle"), ("square", "Square"), ("diamond", "Diamond"), ("triangle", "Triangle"),
    ("star", "Star"), ("plus", "Plus"), ("hexagon", "Hexagon"),
    ("heart", "Heart"), ("smiley", "Smiley"), ("ghost", "Ghost"), ("cat", "Cat"),
    ("rocket", "Rocket"), ("mushroom", "Mushroom"), ("pizza", "Pizza"), ("moustache", "Moustache"),
]
KEYS = [s[0] for s in SYMBOLS]
LABEL = {k: n for k, n in SYMBOLS}
FUNNY = KEYS[7:]

# name, hex. Chosen to stay apart on a projector and in print.
PALETTE = [
    ("Red", "#E03131"), ("Orange", "#F08C00"), ("Yellow", "#E6B800"), ("Green", "#2F9E44"),
    ("Teal", "#0CA678"), ("Blue", "#1C7ED6"), ("Navy", "#1F3A93"), ("Purple", "#7048E8"),
    ("Pink", "#E64980"), ("Brown", "#8B5A2B"), ("Slate", "#495057"),
]
COLORS = {n: h for n, h in PALETTE}
COLOR_NAME = {h: n for n, h in PALETTE}


# ---------------------------------------------------------------------------- drawing helpers
def _poly(n: int, r: float = 42, cx: float = 50, cy: float = 50, rot: float = -90) -> str:
    pts = []
    for i in range(n):
        a = math.radians(rot + 360 * i / n)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def _star(points: int = 5, r1: float = 46, r2: float = 20) -> str:
    pts = []
    for i in range(points * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(-90 + 180 * i / points)
        pts.append(f"{50 + r * math.cos(a):.1f},{50 + r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def _circle(cx: float, cy: float, r: float) -> str:
    """A circle from four cubic curves (no arcs, so the Matplotlib twin can read it)."""
    k = 0.5523 * r
    return (f"M{cx + r},{cy} C{cx + r},{cy + k} {cx + k},{cy + r} {cx},{cy + r} "
            f"C{cx - k},{cy + r} {cx - r},{cy + k} {cx - r},{cy} "
            f"C{cx - r},{cy - k} {cx - k},{cy - r} {cx},{cy - r} "
            f"C{cx + k},{cy - r} {cx + r},{cy - k} {cx + r},{cy} Z")


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> str:
    kx, ky = 0.5523 * rx, 0.5523 * ry
    return (f"M{cx + rx},{cy} C{cx + rx},{cy + ky} {cx + kx},{cy + ry} {cx},{cy + ry} "
            f"C{cx - kx},{cy + ry} {cx - rx},{cy + ky} {cx - rx},{cy} "
            f"C{cx - rx},{cy - ky} {cx - kx},{cy - ry} {cx},{cy - ry} "
            f"C{cx + kx},{cy - ry} {cx + rx},{cy - ky} {cx + rx},{cy} Z")


# Each symbol: (solid parts, holes). Parts never overlap each other; holes sit inside a part.
SHAPES: dict[str, tuple[str, str]] = {
    "circle": (_circle(50, 50, 44), ""),
    "square": ("M10,10 H90 V90 H10 Z", ""),
    "diamond": ("M50,4 L96,50 L50,96 L4,50 Z", ""),
    "triangle": ("M50,8 L94,88 L6,88 Z", ""),
    "star": (_star(), ""),
    "plus": ("M36,6 H64 V36 H94 V64 H64 V94 H36 V64 H6 V36 H36 Z", ""),
    "hexagon": (_poly(6, 46, rot=0), ""),
    # the funny ones
    "heart": ("M50,90 C24,70 6,54 6,32 C6,17 17,7 30,7 C39,7 46,12 50,20 C54,12 61,7 70,7 C83,7 94,17 94,32 "
              "C94,54 76,70 50,90 Z", ""),
    "smiley": (_circle(50, 50, 46), _circle(34, 38, 7) + " " + _circle(66, 38, 7)
               + " M24,58 Q50,88 76,58 Q50,74 24,58 Z"),
    "ghost": ("M50,4 C27,4 12,22 12,46 V94 L25,82 L37,94 L50,82 L63,94 L75,82 L88,94 V46 C88,22 73,4 50,4 Z",
              _ellipse(37, 42, 6, 8) + " " + _ellipse(63, 42, 6, 8)),
    "cat": ("M18,8 L40,30 C46,27 54,27 60,30 L82,8 L84,48 C86,72 70,92 50,92 C30,92 14,72 16,48 Z",
            _ellipse(37, 54, 6, 7) + " " + _ellipse(63, 54, 6, 7) + " M50,66 L44,72 L56,72 Z"),
    "rocket": ("M50,2 C63,14 70,32 70,54 V72 H30 V54 C30,32 37,14 50,2 Z M30,58 L14,80 H30 Z M70,58 L86,80 H70 Z "
               "M38,72 L50,98 L62,72 Z", _circle(50, 40, 8)),
    "mushroom": ("M6,50 C6,24 26,6 50,6 C74,6 94,24 94,50 V56 H6 Z M34,56 L32,86 C32,96 68,96 68,86 L66,56 Z",
                 _circle(30, 32, 7) + " " + _circle(56, 22, 6) + " " + _circle(72, 42, 6)),
    "pizza": ("M50,96 L6,22 C34,6 66,6 94,22 Z", _circle(50, 34, 7) + " " + _circle(34, 48, 6) + " "
              + _circle(62, 54, 6) + " " + _circle(50, 72, 5)),
    "moustache": ("M50,44 C44,22 26,18 16,28 C2,40 2,66 16,74 C30,82 44,74 50,60 C56,74 70,82 84,74 "
                  "C98,66 98,40 84,28 C74,18 56,22 50,44 Z", ""),
}
PATHS = {k: (solid + " " + holes).strip() for k, (solid, holes) in SHAPES.items()}


def path_d(key: str) -> str:
    return PATHS.get(key, PATHS["circle"])


def label(key: str) -> str:
    return LABEL.get(key, "Circle")


# ---------------------------------------------------------------------------- SVG for the page
def svg_text(key: str, color: str, halo: float = 0) -> str:
    """One symbol as SVG. halo > 0 adds a white outline outside the fill (for use on top of bars)."""
    d = path_d(key)
    if halo:
        st = f' stroke="white" stroke-width="{halo}" stroke-linejoin="round" paint-order="stroke"'
        box = f"{-halo} {-halo} {100 + 2 * halo} {100 + 2 * halo}"
    else:
        st, box = "", "0 0 100 100"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}"><path d="{d}" fill="{color}" fill-rule="evenodd"{st}/></svg>')


def data_uri(key: str, color: str, halo: float = 0) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg_text(key, color, halo).encode()).decode()


def svg(key: str, color: str, size: int = 40) -> str:
    """One symbol as an <img> with a data URI (Streamlit strips inline SVG from st.html)."""
    return (f'<img src="{data_uri(key, color)}" width="{size}" height="{size}" alt="{label(key)}" '
            f'style="vertical-align:middle;display:inline-block">')


def badge(key: str, color: str, text: str = "", size: int = 22) -> str:
    """Symbol plus a label, for legends and tables."""
    t = f'<span style="margin-left:.4rem">{text}</span>' if text else ""
    return (f'<span style="display:inline-flex;align-items:center;white-space:nowrap">'
            f'{svg(key, color, size)}{t}</span>')


# ---------------------------------------------------------------------------- Matplotlib twin
_TOKEN = re.compile(r"[MLHVCQZ]|-?\d*\.?\d+")


def _subpaths(d: str) -> list[tuple[tuple[float, float], list[tuple[str, list[tuple[float, float]]]]]]:
    """Parse the absolute M/L/H/V/C/Q/Z commands we use into subpaths: (start, [(kind, points)...])."""
    toks = _TOKEN.findall(d)
    i, cur, start, segs, out = 0, (0.0, 0.0), (0.0, 0.0), [], []

    def nums(n):
        nonlocal i
        vals = [float(toks[i + j]) for j in range(n)]
        i += n
        return vals

    while i < len(toks):
        c = toks[i]
        i += 1
        if c == "M":
            if segs:
                out.append((start, segs))
            x, y = nums(2)
            start = cur = (x, y)
            segs = []
        elif c == "L":
            x, y = nums(2)
            segs.append(("L", [(x, y)]))
            cur = (x, y)
        elif c == "H":
            (x,) = nums(1)
            segs.append(("L", [(x, cur[1])]))
            cur = (x, cur[1])
        elif c == "V":
            (y,) = nums(1)
            segs.append(("L", [(cur[0], y)]))
            cur = (cur[0], y)
        elif c == "C":
            x1, y1, x2, y2, x, y = nums(6)
            segs.append(("C", [(x1, y1), (x2, y2), (x, y)]))
            cur = (x, y)
        elif c == "Q":
            x1, y1, x, y = nums(4)
            segs.append(("Q", [(x1, y1), (x, y)]))
            cur = (x, y)
        elif c == "Z":
            cur = start
    if segs:
        out.append((start, segs))
    return out


def _area(start, segs) -> float:
    """Signed area of the outline, curves sampled, to tell the winding direction."""
    pts = [start]
    prev = start
    for kind, p in segs:
        if kind == "L":
            pts.append(p[0])
        else:
            for t in (0.25, 0.5, 0.75, 1.0):
                if kind == "C":
                    (x1, y1), (x2, y2), (x3, y3) = p
                    x = (1 - t) ** 3 * prev[0] + 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t ** 2 * x2 + t ** 3 * x3
                    y = (1 - t) ** 3 * prev[1] + 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t ** 2 * y2 + t ** 3 * y3
                else:
                    (x1, y1), (x2, y2) = p
                    x = (1 - t) ** 2 * prev[0] + 2 * (1 - t) * t * x1 + t ** 2 * x2
                    y = (1 - t) ** 2 * prev[1] + 2 * (1 - t) * t * y1 + t ** 2 * y2
                pts.append((x, y))
        prev = p[-1]
    a = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        a += x0 * y1 - x1 * y0
    return a / 2


def _reverse(start, segs):
    """The same outline walked the other way round."""
    ends = [start] + [p[-1] for _, p in segs]
    new, s = [], ends[-1]
    for k in range(len(segs) - 1, -1, -1):
        kind, p = segs[k]
        ctrl = list(reversed(p[:-1]))
        new.append((kind, ctrl + [ends[k]]))
    return s, new


@lru_cache(maxsize=None)
def mpl_path(key: str):
    """The symbol as a Matplotlib Path, holes wound the other way so they stay holes under the nonzero rule."""
    from matplotlib.path import Path

    solid, holes = SHAPES.get(key, SHAPES["circle"])
    verts, codes = [], []
    for d, hole in ((solid, False), (holes, True)):
        for start, segs in _subpaths(d):
            a = _area(start, segs)
            if (a < 0) != hole:          # solid parts positive, holes negative
                start, segs = _reverse(start, segs)
            verts.append(start)
            codes.append(Path.MOVETO)
            for kind, p in segs:
                verts.extend(p)
                codes.extend({"L": [Path.LINETO], "C": [Path.CURVE4] * 3, "Q": [Path.CURVE3] * 2}[kind])
            verts.append(start)
            codes.append(Path.CLOSEPOLY)
    # flip y (SVG grows downwards) and centre on the origin
    verts = [(x - 50, 50 - y) for x, y in verts]
    return Path(verts, codes)
