#!/usr/bin/env python3
"""Draws the Ballooniverse card: an original balloon with a home and three dots on a starry sky."""
import math
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Polygon, Circle, Rectangle

random.seed(7)
W, H = 8.0, 4.0
fig, ax = plt.subplots(figsize=(W, H), dpi=110)
ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)
ax.add_patch(Rectangle((0, 0), W, H, color="#081a2e"))
# stars
for _ in range(140):
    x, y = random.uniform(0, W), random.uniform(0, H)
    ax.add_patch(Circle((x, y), random.uniform(0.004, 0.018), color="white", alpha=random.uniform(0.35, 1)))
# a faint nebula glow
for r, a in ((2.4, .05), (1.8, .06), (1.2, .08)):
    ax.add_patch(Ellipse((5.9, 2.4), r * 2.2, r * 1.3, color="#4f7fbf", alpha=a))
# balloon body: layered ellipses give it a little shading
cx, cy = 3.1, 2.35
for k, (dx, dy, col) in enumerate(((0, 0, "#1c4f8f"), (-0.05, 0.05, "#2563a8"), (-0.14, 0.14, "#2f74bf"))):
    ax.add_patch(Ellipse((cx + dx, cy + dy), 2.5 - 0.22 * k, 3.0 - 0.3 * k, color=col))
ax.add_patch(Ellipse((cx - 0.48, cy + 0.85), 0.5, 0.95, angle=25, color="white", alpha=0.18))
# knot and string
ax.add_patch(Polygon([[cx - 0.13, cy - 1.48], [cx + 0.13, cy - 1.48], [cx, cy - 1.3]], color="#1c4f8f"))
t = [i / 60 for i in range(61)]
ax.plot([cx + 0.18 * math.sin(6.5 * s) for s in t], [cy - 1.48 - 1.0 * s for s in t], color="#9cc9e8", lw=1.2)
# home symbol
hx, hy = cx - 0.55, cy - 0.15
ax.add_patch(Rectangle((hx - 0.13, hy - 0.12), 0.26, 0.2, color="#f6f1e7"))
ax.add_patch(Polygon([[hx - 0.18, hy + 0.08], [hx + 0.18, hy + 0.08], [hx, hy + 0.3]], color="#E03131"))
# three dots, near, middle, far, with little labels
for (dx, dy, col, lab) in ((0.35, 0.05, "#F08C00", "1"), (0.78, 0.72, "#2F9E44", "2"), (-0.25, 1.1, "#E64980", "3")):
    ax.add_patch(Circle((cx + dx, cy + dy), 0.09, color=col))
    ax.text(cx + dx + 0.14, cy + dy + 0.1, lab, color="white", fontsize=9, fontweight="bold")
# a wavy line
xs = [cx + 0.15 + 0.012 * i for i in range(50)]
ax.plot(xs, [cy - 0.75 + 0.07 * math.sin(i / 2.3) for i in range(50)], color="#f6f1e7", lw=1.6)
fig.savefig("assets/img/balloon.png", dpi=110)
print("balloon ok")
