"""The live boards (Plotly) and their printable twins (Matplotlib) for the Excel export."""
from __future__ import annotations

import io
import math

import plotly.graph_objects as go

from tag import icons
from tag.stats import fit_through_origin, fmt, summary

FONT = "Barlow, Arial, sans-serif"
INK = "#18202C"
MUTED = "#5E6878"
NAVY = "#0C2340"
BAND = "rgba(31,90,166,.14)"


# =============================================================================== two-point threshold
def tpt_people(room: dict) -> list[dict]:
    """One row per participant with data: name, pair label, icon, colour, thumb mean, forearm mean."""
    rows = []
    for pid in room["order"]:
        p = room["pairs"].get(pid)
        if not p or not p.get("data"):
            continue
        for person in p["data"].get("people", []):
            th = [v for v in person.get("thumb", []) if v is not None]
            fa = [v for v in person.get("forearm", []) if v is not None]
            if not person.get("name") or not th or not fa:
                continue
            rows.append({"name": person["name"], "pair": p["label"], "icon": p["icon"], "color": p["color"],
                         "thumb": sum(th) / len(th), "forearm": sum(fa) / len(fa),
                         "thumb_trials": th, "forearm_trials": fa})
    return rows


BIN = 5.0                 # mm, as on the seminar slide
THUMB = "#2E7F7A"
FOREARM = "#C8352B"
THUMB_D = "#1D5956"
FOREARM_D = "#8C2019"


def _hist(vals, w: float = BIN) -> dict[int, int]:
    """Counts per bin index (bin b covers [b*w, (b+1)*w))."""
    counts: dict[int, int] = {}
    for v in vals:
        b = int(math.floor(v / w + 1e-9))
        counts[b] = counts.get(b, 0) + 1
    return counts


def _stack(rows: list[dict], key: str, frac: float, w: float = BIN):
    """Where each person's symbol sits inside its bar: x a fraction into the bin, y 0.5, 1.5, ... in arrival order."""
    seen: dict[int, int] = {}
    out = []
    for r in rows:
        b = int(math.floor(r[key] / w + 1e-9))
        seen[b] = seen.get(b, 0) + 1
        out.append(((b + frac) * w, seen[b] - 0.5))
    return out


def _tpt_frame(rows: list[dict]):
    th, fa = _hist(r["thumb"] for r in rows), _hist(r["forearm"] for r in rows)
    top = max(max(th.values()), max(fa.values()))
    xmax = max(40.0, (max(list(th) + list(fa)) + 1) * BIN)
    ymax = top + max(1.5, top * 0.18)
    return th, fa, top, xmax, ymax


def _rgba(hexcolor: str, a: float) -> str:
    h = hexcolor.lstrip("#")
    return f"rgba({int(h[:2], 16)},{int(h[2:4], 16)},{int(h[4:], 16)},{a})"


def tpt_figure(rows: list[dict], big: bool = True, show_stats: bool = False) -> go.Figure:
    """The slide's histogram: thumb and forearm on the same axis, 5 mm bins, one count per student.
    Each student's symbol is stacked inside the bar so a pair can find itself."""
    fig = go.Figure()
    n = len(rows)
    if not rows:
        fig.add_annotation(text="Waiting for the first numbers…", xref="paper", yref="paper", x=0.5, y=0.45,
                           showarrow=False, font=dict(size=22 if big else 14, color=MUTED))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        th, fa, top, xmax, ymax = _tpt_frame(rows)
        for counts, name, color, alpha in ((th, "Thumb (mm)", THUMB, 1.0), (fa, "Forearm (mm)", FOREARM, 0.85)):
            bins = sorted(counts)
            fig.add_trace(go.Bar(
                x=[(b + 0.5) * BIN for b in bins], y=[counts[b] for b in bins], width=BIN, name=name,
                marker=dict(color=color, line=dict(color="white", width=1)), opacity=alpha,
                customdata=[[b * BIN, (b + 1) * BIN] for b in bins],
                hovertemplate=name.split()[0] + ": %{y} students<br>%{customdata[0]:g} to %{customdata[1]:g} mm<extra></extra>"))
        area = (520 - 120) if big else (300 - 80)          # plot height in px, roughly
        ms = max(8 if big else 6, min(22 if big else 13, 0.68 * area / ymax))
        for key, frac in (("thumb", 0.27), ("forearm", 0.73)):
            pos = _stack(rows, key, frac)
            by_pair: dict[str, list[int]] = {}
            for i, r in enumerate(rows):
                by_pair.setdefault(r["pair"], []).append(i)
            for label, idx in by_pair.items():
                r0 = rows[idx[0]]
                fig.add_trace(go.Scatter(
                    x=[pos[i][0] for i in idx], y=[pos[i][1] for i in idx], mode="markers", name=label, showlegend=False,
                    marker=dict(symbol=icons.PLOTLY[r0["icon"]], color=r0["color"], size=ms, line=dict(width=1, color="white")),
                    customdata=[[rows[i]["name"], rows[i]["pair"], rows[i][key]] for i in idx],
                    hovertemplate="%{customdata[0]} (%{customdata[1]})<br>" + key + " %{customdata[2]:.2f} mm<extra></extra>"))
        if show_stats:
            for key, color, dark, side in (("thumb", THUMB, THUMB_D, "left"), ("forearm", FOREARM, FOREARM_D, "right")):
                s = summary([r[key] for r in rows])
                if s["n"] < 2:
                    continue
                fig.add_vrect(x0=s["lo"], x1=s["hi"], fillcolor=_rgba(color, 0.16), line_width=0, layer="above")
                fig.add_vline(x=s["mean"], line=dict(color=dark, width=3, dash="dash"))
                fig.add_annotation(x=s["mean"], y=ymax, text=f"{key} mean {fmt(s['mean'], 1)} mm<br>95%: {fmt(s['lo'], 1)} to {fmt(s['hi'], 1)}",
                                   showarrow=False, yanchor="top", xanchor=side, xshift=-6 if side == "right" else 6,
                                   font=dict(size=15 if big else 11, color=dark), bgcolor="rgba(255,255,255,.85)")
        fig.update_xaxes(title_text="Two-point threshold (mm)", range=[-0.6, xmax + 0.6], dtick=5, tick0=0, showgrid=False,
                         zeroline=False, ticks="outside", tickcolor="#C9CED6")
        fig.update_yaxes(title_text="Number of students", range=[0, ymax], dtick=1 if top <= 12 else (2 if top <= 30 else 5),
                         showgrid=True, gridcolor="#E9ECEF", zeroline=False)
    title = (f"Thumb and forearm on the same axis · {n} {'student' if n == 1 else 'students'} · 5 mm bins"
             if (rows and big) else "")
    fig.update_layout(barmode="overlay", height=520 if big else 300, margin=dict(l=20, r=20, t=60 if big else 30, b=50),
                      paper_bgcolor="white", plot_bgcolor="white", font=dict(family=FONT, size=16 if big else 12, color=INK),
                      title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20, color=NAVY)),
                      showlegend=bool(rows), legend=dict(x=0.99, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(255,255,255,.8)",
                                                        font=dict(size=16 if big else 11)),
                      hovermode="closest")
    return fig


def tpt_png(rows: list[dict], title: str = "", show_stats: bool = False) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 5.6), dpi=150)
    ax.set_xlabel("Two-point threshold (mm)")
    ax.set_ylabel("Number of students")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    if not rows:
        ax.text(0.5, 0.5, "no data", transform=ax.transAxes, ha="center", color=MUTED)
    else:
        th, fa, top, xmax, ymax = _tpt_frame(rows)
        for counts, name, color, alpha in ((th, "Thumb (mm)", THUMB, 1.0), (fa, "Forearm (mm)", FOREARM, 0.85)):
            bins = sorted(counts)
            ax.bar([(b + 0.5) * BIN for b in bins], [counts[b] for b in bins], width=BIN, color=color, alpha=alpha,
                   edgecolor="white", linewidth=1, label=name)
        ms = max(4.5, min(13.0, 0.62 * 300 / ymax))
        for key, frac in (("thumb", 0.27), ("forearm", 0.73)):
            for r, (x, y) in zip(rows, _stack(rows, key, frac)):
                ax.plot(x, y, marker=icons.MPL[r["icon"]], color=r["color"], ms=ms, ls="", mec="white", mew=0.6)
        if show_stats:
            for key, color, dark in (("thumb", THUMB, THUMB_D), ("forearm", FOREARM, FOREARM_D)):
                s = summary([r[key] for r in rows])
                if s["n"] >= 2:
                    ax.axvspan(s["lo"], s["hi"], color=color, alpha=0.16, lw=0)
                    ax.axvline(s["mean"], color=dark, lw=2, ls="--")
        ax.set_xlim(-0.6, xmax + 0.6)
        ax.set_xticks(range(0, int(xmax) + 1, 5))
        ax.set_ylim(0, ymax)
        ax.yaxis.grid(color="#E9ECEF")
        ax.set_axisbelow(True)
        ax.legend(loc="upper right", frameon=False)
        ax.set_title(f"Thumb and forearm on the same axis ({len(rows)} students, 5 mm bins)" + (f"\n{title}" if title else ""),
                     fontsize=12, color=NAVY)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


# =============================================================================== ballooniverse
def balloon_points(room: dict) -> list[dict]:
    """One row per dot: pair, dot number, initial, final, change, velocity."""
    t = float(room["settings"].get("inflate_s", 10) or 10)
    rows = []
    for pid in room["order"]:
        p = room["pairs"].get(pid)
        if not p or not p.get("data"):
            continue
        d = p["data"]
        for i in range(3):
            a, b = d["init"][i], d["final"][i]
            if a is None or b is None:
                continue
            rows.append({"pair": p["label"], "icon": p["icon"], "color": p["color"], "dot": i + 1,
                         "init": a, "final": b, "change": b - a, "v": (b - a) / t})
    return rows


LINE = "#111111"


def _balloon_frame(rows: list[dict]):
    xmax = max(r["final"] for r in rows) * 1.08
    ymax = max(max(r["v"] for r in rows), 0) * 1.15
    ymin = min(min(r["v"] for r in rows), 0) * 1.15
    return xmax, (ymax if ymax > 0 else 1), min(ymin, 0)


def _formula(t: float) -> str:
    return f"velocity = (final distance − initial distance) ÷ {t:g} s"


def balloon_figure(rows: list[dict], trend: bool = True, big: bool = True, t: float = 10.0) -> go.Figure:
    """The slide's scatter: velocity away from home against final distance, best-fit line through the origin."""
    fig = go.Figure()
    by_pair: dict[str, list[dict]] = {}
    for r in rows:
        by_pair.setdefault(r["pair"], []).append(r)
    ms = 18 if big else 12
    for label, pts in by_pair.items():
        fig.add_trace(go.Scatter(
            x=[r["final"] for r in pts], y=[r["v"] for r in pts], mode="markers", name=label,
            marker=dict(symbol=icons.PLOTLY[pts[0]["icon"]], color=pts[0]["color"], size=ms, line=dict(width=1.2, color="white")),
            customdata=[[r["pair"], r["dot"], r["init"], r["final"]] for r in pts],
            hovertemplate="%{customdata[0]}, dot %{customdata[1]}<br>final %{x:.0f} mm, velocity %{y:.2f} mm/s"
                          "<br>initial %{customdata[2]:.0f} mm<extra></extra>"))
    if rows:
        xmax, ymax, ymin = _balloon_frame(rows)
    else:
        xmax, ymax, ymin = 500, 50, 0
        fig.add_annotation(text="Waiting for the first dots…", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20 if big else 14, color=MUTED))
    if trend and len(rows) >= 2:
        f = fit_through_origin([r["final"] for r in rows], [r["v"] for r in rows])
        if not math.isnan(f["k"]):
            fig.add_trace(go.Scatter(x=[0, xmax], y=[0, f["k"] * xmax], mode="lines", name="trend",
                                     line=dict(color=LINE, width=3), hoverinfo="skip", showlegend=False))
            xa = xmax * 0.42
            fig.add_annotation(x=xa, y=f["k"] * xa + ymax * 0.2, text=f"best-fit line: slope = {fmt(f['k'], 3)} per second",
                               xanchor="center", yanchor="bottom", showarrow=False,
                               font=dict(size=18 if big else 12, color=INK), bgcolor="rgba(255,255,255,.85)")
    fig.update_xaxes(title_text="Final distance from home (mm)", range=[0, xmax], showgrid=True, gridcolor="#E9ECEF",
                     zeroline=True, zerolinecolor="#C9CED6", ticks="outside", tickcolor="#C9CED6")
    fig.update_yaxes(title_text="Velocity away from home (mm/s)", range=[ymin, ymax], showgrid=True,
                     gridcolor="#E9ECEF", zeroline=True, zerolinecolor="#C9CED6", ticks="outside", tickcolor="#C9CED6")
    fig.update_layout(height=560 if big else 320, margin=dict(l=20, r=20, t=62 if big else 42, b=50), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=FONT, size=16 if big else 12, color=INK),
                      title=dict(text=f"<b>{_formula(t)}</b>", x=0.5, xanchor="center", font=dict(size=22 if big else 13, color=INK)),
                      showlegend=False, hovermode="closest")
    return fig


def balloon_png(rows: list[dict], title: str = "", trend: bool = True, t: float = 10.0) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    seen = set()
    for r in rows:
        lab = r["pair"] if r["pair"] not in seen else None
        seen.add(r["pair"])
        ax.plot(r["final"], r["v"], marker=icons.MPL[r["icon"]], color=r["color"], ms=10, ls="", mec="white", mew=0.8, label=lab)
    if rows:
        xmax, ymax, ymin = _balloon_frame(rows)
        if trend and len(rows) >= 2:
            f = fit_through_origin([r["final"] for r in rows], [r["v"] for r in rows])
            if not math.isnan(f["k"]):
                ax.plot([0, xmax], [0, f["k"] * xmax], color=LINE, lw=2)
                xa = xmax * 0.45
                ax.text(xa, f["k"] * xa + ymax * 0.2, f"best-fit line: slope = {fmt(f['k'], 3)} per second   (R² = {fmt(f['r2'], 2)})",
                        ha="center", va="bottom", color=INK, fontsize=11)
        ax.set_xlim(0, xmax)
        ax.set_ylim(ymin, ymax)
    ax.set_xlabel("Final distance from home (mm)")
    ax.set_ylabel("Velocity away from home (mm/s)")
    ax.grid(color="#E9ECEF")
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    if seen:
        ax.legend(loc="upper left", fontsize=9, frameon=False, ncol=2)
    ax.set_title(_formula(t) + (f"\n{title}" if title else ""), fontsize=12, color=INK, fontweight="bold")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()
