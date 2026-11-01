"""The eleven pair symbols and the colour palette.

Each symbol exists three ways: as an SVG for the picker, as a Plotly marker for the
live board, and as a Matplotlib marker for the Excel export, so a pair looks the same
everywhere.
"""
from __future__ import annotations

import math

# key, label, plotly symbol, matplotlib marker
SYMBOLS = [
    ("circle", "Circle", "circle", "o"),
    ("square", "Square", "square", "s"),
    ("diamond", "Diamond", "diamond", "D"),
    ("triangle", "Triangle", "triangle-up", "^"),
    ("wedge", "Wedge", "triangle-down", "v"),
    ("pentagon", "Pentagon", "pentagon", "p"),
    ("hexagon", "Hexagon", "hexagon", "h"),
    ("star", "Star", "star", "*"),
    ("plus", "Plus", "cross", "P"),
    ("cross", "Cross", "x", "X"),
    ("octagon", "Octagon", "octagon", "8"),
]
KEYS = [s[0] for s in SYMBOLS]
LABEL = {k: n for k, n, _, _ in SYMBOLS}
PLOTLY = {k: p for k, _, p, _ in SYMBOLS}
MPL = {k: m for k, _, _, m in SYMBOLS}

# name, hex. Chosen to stay apart on a projector and in print.
PALETTE = [
    ("Red", "#E03131"), ("Orange", "#F08C00"), ("Yellow", "#E6B800"), ("Green", "#2F9E44"),
    ("Teal", "#0CA678"), ("Blue", "#1C7ED6"), ("Navy", "#1F3A93"), ("Purple", "#7048E8"),
    ("Pink", "#E64980"), ("Brown", "#8B5A2B"), ("Slate", "#495057"),
]
COLORS = {n: h for n, h in PALETTE}
COLOR_NAME = {h: n for n, h in PALETTE}


def _poly(n: int, r: float = 42, cx: float = 50, cy: float = 50, rot: float = -90) -> str:
    pts = []
    for i in range(n):
        a = math.radians(rot + 360 * i / n)
        pts.append(f"{cx + r * math.cos(a):.1f},{cy + r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


def _star(points: int = 5, r1: float = 44, r2: float = 19) -> str:
    pts = []
    for i in range(points * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(-90 + 180 * i / points)
        pts.append(f"{50 + r * math.cos(a):.1f},{50 + r * math.sin(a):.1f}")
    return "M" + " L".join(pts) + " Z"


PATHS = {
    "circle": "M50,8 A42,42 0 1,0 50,92 A42,42 0 1,0 50,8 Z",
    "square": "M12,12 H88 V88 H12 Z",
    "diamond": "M50,6 L94,50 L50,94 L6,50 Z",
    "triangle": "M50,10 L92,86 L8,86 Z",
    "wedge": "M8,14 L92,14 L50,90 Z",
    "pentagon": _poly(5, 44),
    "hexagon": _poly(6, 44, rot=0),
    "star": _star(),
    "plus": "M38,8 H62 V38 H92 V62 H62 V92 H38 V62 H8 V38 H38 Z",
    "cross": "M22,8 L50,36 L78,8 L92,22 L64,50 L92,78 L78,92 L50,64 L22,92 L8,78 L36,50 L8,22 Z",
    "octagon": _poly(8, 45, rot=22.5),
}


def svg_text(key: str, color: str, stroke: str | None = None) -> str:
    d = PATHS[key]
    st = f' stroke="{stroke}" stroke-width="4" stroke-linejoin="round"' if stroke else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="{d}" fill="{color}"{st}/></svg>')


def svg(key: str, color: str, size: int = 40, stroke: str | None = None) -> str:
    """One symbol as an <img> with a data URI (Streamlit strips inline SVG from st.html)."""
    import base64
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg_text(key, color, stroke).encode()).decode()
    return (f'<img src="{uri}" width="{size}" height="{size}" alt="{LABEL[key]}" '
            f'style="vertical-align:middle;display:inline-block">')


def badge(key: str, color: str, label: str = "", size: int = 22) -> str:
    """Symbol plus a label, for legends and tables."""
    text = f'<span style="margin-left:.4rem">{label}</span>' if label else ""
    return (f'<span style="display:inline-flex;align-items:center;white-space:nowrap">'
            f'{svg(key, color, size)}{text}</span>')
