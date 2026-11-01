"""The live boards (Plotly) and their printable twins (Matplotlib) for the Excel export."""
from __future__ import annotations

import io
import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tag import icons
from tag.stats import dot_stack, fit_through_origin, fmt, nice_bin, summary

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


def _dot_panel(fig, rows: list[dict], key: str, col: int, big: bool):
    vals = [r[key] for r in rows]
    lo, hi = min(vals), max(vals)
    w = nice_bin(min(lo, 0 if key == "thumb" else lo), hi, 14 if big else 10)
    pos = dot_stack(vals, w)
    s = summary(vals)
    n = len(vals)
    ms = (24 if n <= 8 else 20 if n <= 24 else 16) if big else 13
    # one trace per pair so the legend groups by pair symbol
    by_pair: dict[str, list[int]] = {}
    for i, r in enumerate(rows):
        by_pair.setdefault(r["pair"], []).append(i)
    for label, idx in by_pair.items():
        r0 = rows[idx[0]]
        fig.add_trace(go.Scatter(
            x=[pos[i][0] for i in idx], y=[pos[i][1] for i in idx], mode="markers", name=label,
            marker=dict(symbol=icons.PLOTLY[r0["icon"]], color=r0["color"], size=ms, line=dict(width=1.2, color="white")),
            customdata=[[rows[i]["name"], rows[i]["pair"], rows[i][key]] for i in idx],
            hovertemplate="%{customdata[0]} (%{customdata[1]})<br>%{customdata[2]:.2f} mm<extra></extra>",
            showlegend=(col == 1), legendgroup=label), row=1, col=col)
    top = max(k for _, k in pos)
    ymax = top + 1
    if s["n"] >= 2:
        fig.add_vrect(x0=s["lo"], x1=s["hi"], fillcolor=BAND, line_width=0, row=1, col=col)
        fig.add_vline(x=s["mean"], line=dict(color=NAVY, width=3), row=1, col=col)
        fig.add_annotation(x=s["mean"], y=top + 1.2, text=f"mean {fmt(s['mean'], 1)} mm", showarrow=False, yanchor="bottom",
                           font=dict(size=17 if big else 12, color=NAVY), row=1, col=col)
        fig.add_annotation(x=s["mean"], y=top + 1.2 + (top + 2) * 0.17, text=f"95%: {fmt(s['lo'], 1)} to {fmt(s['hi'], 1)}",
                           showarrow=False, yanchor="bottom", font=dict(size=13 if big else 11, color=MUTED), row=1, col=col)
    x0 = min(lo, s["lo"] if s["n"] >= 2 else lo) - 2.5 * w
    x1 = max(hi, s["hi"] if s["n"] >= 2 else hi) + 2.5 * w
    x0 = max(0.0, x0)
    tick = nice_bin(x0, x1, 8)
    fig.update_yaxes(range=[0.3, (top + 2) * 1.45 + 0.5], showticklabels=False, showgrid=False, zeroline=False, row=1, col=col)
    fig.update_xaxes(title_text="two-point threshold (mm)", range=[x0, x1], dtick=tick, tick0=0,
                     showgrid=False, zeroline=False, row=1, col=col)


def tpt_figure(rows: list[dict], big: bool = True) -> go.Figure:
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Thumb", "Forearm"), horizontal_spacing=0.07)
    for a in fig.layout.annotations[:2]:
        a.font = dict(size=26 if big else 16, color=NAVY, family=FONT)
    if not rows:
        fig.add_annotation(text="Waiting for the first numbers…", xref="paper", yref="paper", x=0.5, y=0.45,
                           showarrow=False, font=dict(size=22 if big else 14, color=MUTED))
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
    else:
        _dot_panel(fig, rows, "thumb", 1, big)
        _dot_panel(fig, rows, "forearm", 2, big)
    fig.update_layout(height=500 if big else 300, margin=dict(l=20, r=20, t=60, b=50), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=FONT, size=16 if big else 12, color=INK),
                      showlegend=False, hovermode="closest")
    return fig


def tpt_png(rows: list[dict], title: str = "") -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), dpi=150)
    for ax, key, name in zip(axes, ("thumb", "forearm"), ("Thumb", "Forearm")):
        vals = [r[key] for r in rows]
        ax.set_title(name, fontsize=16, color=NAVY, fontweight="bold")
        ax.set_xlabel("two-point threshold (mm)")
        ax.set_yticks([])
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        if not vals:
            ax.text(0.5, 0.5, "no data", transform=ax.transAxes, ha="center", color=MUTED)
            continue
        w = nice_bin(min(min(vals), 0 if key == "thumb" else min(vals)), max(vals), 14)
        pos = dot_stack(vals, w)
        s = summary(vals)
        seen = set()
        for r, (x, k) in zip(rows, pos):
            lab = r["pair"] if r["pair"] not in seen else None
            seen.add(r["pair"])
            ax.plot(x, k, marker=icons.MPL[r["icon"]], color=r["color"], ms=12, ls="", mec="white", mew=0.8, label=lab)
        ymax = max(k for _, k in pos) + 1
        if s["n"] >= 2:
            ax.axvspan(s["lo"], s["hi"], color="#1F5AA6", alpha=0.14, lw=0)
            ax.axvline(s["mean"], color=NAVY, lw=2.5)
            ax.text(s["mean"], ymax + 0.2, f"mean {fmt(s['mean'], 1)} mm\n95%: {fmt(s['lo'], 1)} to {fmt(s['hi'], 1)}",
                    ha="center", va="bottom", color=NAVY, fontsize=10)
        ax.set_ylim(0.3, (ymax + 1) * 1.45 + 0.5)
        x0 = max(0.0, min(min(vals), s["lo"] if s["n"] >= 2 else min(vals)) - 2.5 * w)
        x1 = max(max(vals), s["hi"] if s["n"] >= 2 else max(vals)) + 2.5 * w
        ax.set_xlim(x0, x1)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=min(6, len(handles)), frameon=False, fontsize=9,
                   bbox_to_anchor=(0.5, -0.02))
    if title:
        fig.suptitle(title, fontsize=13, color=MUTED, y=0.995)
    fig.tight_layout(rect=(0, 0.08 if handles else 0, 1, 0.97))
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


def balloon_figure(rows: list[dict], trend: bool = True, big: bool = True) -> go.Figure:
    fig = go.Figure()
    by_pair: dict[str, list[dict]] = {}
    for r in rows:
        by_pair.setdefault(r["pair"], []).append(r)
    ms = 20 if big else 13
    for label, pts in by_pair.items():
        fig.add_trace(go.Scatter(
            x=[r["final"] for r in pts], y=[r["v"] for r in pts], mode="markers", name=label,
            marker=dict(symbol=icons.PLOTLY[pts[0]["icon"]], color=pts[0]["color"], size=ms, line=dict(width=1.2, color="white")),
            customdata=[[r["pair"], r["dot"], r["init"], r["final"]] for r in pts],
            hovertemplate="%{customdata[0]}, dot %{customdata[1]}<br>final %{x:.0f} mm, velocity %{y:.2f} mm/s"
                          "<br>initial %{customdata[2]:.0f} mm<extra></extra>"))
    if rows:
        xmax = max(r["final"] for r in rows) * 1.08
        ymax = max(max(r["v"] for r in rows), 0) * 1.15
        ymin = min(min(r["v"] for r in rows), 0) * 1.15
    else:
        xmax, ymax, ymin = 200, 20, 0
        fig.add_annotation(text="Waiting for the first dots…", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
                           font=dict(size=20 if big else 14, color=MUTED))
    if trend and len(rows) >= 2:
        f = fit_through_origin([r["final"] for r in rows], [r["v"] for r in rows])
        if not math.isnan(f["k"]):
            fig.add_trace(go.Scatter(x=[0, xmax], y=[0, f["k"] * xmax], mode="lines", name="trend",
                                     line=dict(color=NAVY, width=3, dash="dash"), hoverinfo="skip", showlegend=False))
            fig.add_annotation(x=xmax * 0.98, y=f["k"] * xmax, text=f"v ≈ {fmt(f['k'], 3)} × d", xanchor="right",
                               yanchor="bottom", showarrow=False, font=dict(size=18 if big else 12, color=NAVY))
    fig.update_xaxes(title_text="final distance from home, d (mm)", range=[0, xmax], showgrid=True, gridcolor="#EEF0F3",
                     zeroline=True, zerolinecolor="#C9CED6")
    fig.update_yaxes(title_text="velocity, v (mm/s)", range=[min(ymin, 0), ymax if ymax > 0 else 1], showgrid=True,
                     gridcolor="#EEF0F3", zeroline=True, zerolinecolor="#C9CED6")
    fig.update_layout(height=560 if big else 320, margin=dict(l=20, r=20, t=30, b=50), paper_bgcolor="white",
                      plot_bgcolor="white", font=dict(family=FONT, size=16 if big else 12, color=INK),
                      showlegend=False, hovermode="closest")
    return fig


def balloon_png(rows: list[dict], title: str = "", trend: bool = True) -> bytes:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    seen = set()
    for r in rows:
        lab = r["pair"] if r["pair"] not in seen else None
        seen.add(r["pair"])
        ax.plot(r["final"], r["v"], marker=icons.MPL[r["icon"]], color=r["color"], ms=11, ls="", mec="white", mew=0.8, label=lab)
    if rows:
        xmax = max(r["final"] for r in rows) * 1.08
        if trend and len(rows) >= 2:
            f = fit_through_origin([r["final"] for r in rows], [r["v"] for r in rows])
            if not math.isnan(f["k"]):
                ax.plot([0, xmax], [0, f["k"] * xmax], ls="--", color=NAVY, lw=2)
                ax.text(xmax * 0.98, f["k"] * xmax, f"v ≈ {fmt(f['k'], 3)} × d   (R² = {fmt(f['r2'], 2)})", ha="right",
                        va="bottom", color=NAVY, fontsize=11)
        ax.set_xlim(0, xmax)
        ymin = min(min(r["v"] for r in rows), 0) * 1.15
        ax.set_ylim(ymin, max(r["v"] for r in rows) * 1.15 if max(r["v"] for r in rows) > 0 else 1)
    ax.set_xlabel("final distance from home, d (mm)")
    ax.set_ylabel("velocity, v (mm/s)")
    ax.grid(color="#EEF0F3")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    if seen:
        ax.legend(loc="upper left", fontsize=9, frameon=False, ncol=2)
    if title:
        ax.set_title(title, fontsize=13, color=MUTED)
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()
