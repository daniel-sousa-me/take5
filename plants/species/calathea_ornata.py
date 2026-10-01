"""Calathea ornata (pinstripe calathea) - v4.

Basal clump of long, thin, upright petioles, each ending in a small pulvinus
and an elliptic-oblong, acuminate leaf. Upper surface very dark green with
paired blush pinstripes that leave the midrib and follow the lateral-vein
curve toward the margin. Two leaves are turned to show the burgundy underside.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import PAL, Leaf, leaf_g, stem, line, f, T, pot, svg_doc, reset_ids, cr_path  # noqa: E402

P = PAL
CX, RIM_Y, RX = 300, 584, 100

# leaf tones: back -> front. Neighbouring layers differ by >= 1 palette step and
# overlapping pairs are arranged to differ by 2.
TONE = {
    "back": ("#27392C", "#223326"),      # night, a touch darker shade half
    "mid": ("#314B37", "#29402F"),       # deep
    "front": ("#405D43", "#37523B"),     # forest
}
STRIPE = P["blush"]
MIDRIB = "#6F8566"   # sage pulled one step toward the dark leaf, opaque
# petiole / pulvinus tones per layer so crossing petioles stay separable
PET = {
    "back": ("#4B6349", P["mid"]),
    "mid": (P["mid"], P["sage"]),
    "front": (P["sage"], P["light"]),
}
UNDER = (P["burgundy"], P["wine"])


def leaf_shape(L, seed, narrow=1.0, bend=None, sway=0.0):
    rnd = random.Random(seed)
    j = lambda: rnd.uniform(-0.012, 0.012)  # noqa: E731
    right = [(0.02, 0.09), (0.11, 0.205 + j()), (0.28, 0.27 + j()), (0.48, 0.28 + j()),
             (0.67, 0.24 + j()), (0.82, 0.165), (0.915, 0.085), (0.965, 0.035)]
    left = [(0.02, 0.085), (0.12, 0.2 + j()), (0.30, 0.265 + j()), (0.50, 0.275 + j()),
            (0.69, 0.23 + j()), (0.83, 0.155), (0.92, 0.08), (0.967, 0.032)]
    right = [(t, w * narrow) for t, w in right]
    left = [(t, w * narrow) for t, w in left]
    b = rnd.uniform(-0.05, 0.05)
    return Leaf(L, right, left, bend=b if bend is None else bend, sway=sway, base_sharp=False, tip_t=1.0)


def pinstripe(p0, p1, p2, w):
    """Quadratic centre line p0-p1-p2 drawn as a filled stripe: two cubics with
    offset handles, so it is ~w wide over its middle and pointed at both ends.
    Opaque; widest point = w units."""
    c1 = (p0[0] + (p1[0] - p0[0]) * 2 / 3, p0[1] + (p1[1] - p0[1]) * 2 / 3)
    c2 = (p2[0] + (p1[0] - p2[0]) * 2 / 3, p2[1] + (p1[1] - p2[1]) * 2 / 3)

    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        return -dy / m * w / 1.5, dx / m * w / 1.5
    n1, n2 = nrm(p0, p1), nrm(p1, p2)
    return (f"M{f(p0[0])} {f(p0[1])}C{f(c1[0] + n1[0])} {f(c1[1] + n1[1])} {f(c2[0] + n2[0])} "
            f"{f(c2[1] + n2[1])} {f(p2[0])} {f(p2[1])}C{f(c2[0] - n2[0])} {f(c2[1] - n2[1])} "
            f"{f(c1[0] - n1[0])} {f(c1[1] - n1[1])} {f(p0[0])} {f(p0[1])}Z")


STRIPE_W = 4.4      # widest point, units (knockout minimum is 4.0)
PAIR_SEP = 11.0     # axial distance between the two lines of a pair, units
PAIR_STEP = 34.0    # minimum axial distance between successive pairs, units


def stripes(leaf, seed):
    """Paired pinstripes from beside the midrib toward the margin, curving
    tipward. Few, well-spaced pairs of filled tapered strokes so the dark
    ground stays dominant."""
    rnd = random.Random(seed + 99)
    L = leaf.L
    step = max(0.17, PAIR_STEP / L)
    sep = PAIR_SEP / L
    d = []
    t = 0.12
    while t + sep < 0.76:
        for s, sg in (("r", 1), ("l", -1)):
            to = t + rnd.uniform(-0.01, 0.01) + (0.03 if s == "l" else 0.0)
            for k in (0, 1):  # the pair
                t0 = to + k * sep
                dt = 0.16 - 0.06 * t0
                w_end = leaf.width(t0 + dt, s) * 0.84
                p0 = leaf.pt(t0, sg * 0.016)
                p1 = leaf.pt(t0 + dt * 0.36, sg * leaf.width(t0 + dt * 0.36, s) * 0.46)
                p2 = leaf.pt(t0 + dt, sg * w_end)
                d.append(pinstripe(p0, p1, p2, STRIPE_W))
        t += step + rnd.uniform(-0.01, 0.01)
    return f'<path d="{"".join(d)}" fill="{STRIPE}"/>'


def midrib(leaf, col, w0=4.6, w1=1.8, t1=0.9):
    """Opaque tapered midrib (filled), >= 4 units at the base."""
    pts = [leaf.axis(t1 * i / 10) for i in range(11)]
    n = len(pts)
    Lp, Rp = [], []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        m = math.hypot(dx, dy) or 1
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        Lp.append((p[0] - dy / m * w, p[1] + dx / m * w))
        Rp.append((p[0] + dy / m * w, p[1] - dx / m * w))
    return f'<path d="{cr_path(Lp + Rp[::-1], closed=True, sharp={0, n - 1, n, 2 * n - 1})}" fill="{col}"/>'


def unit(deg):
    a = math.radians(deg)
    return math.sin(a), -math.cos(a)


def plant_leaf(spec):
    (sx, bx, by, ang, L, layer, seed, bow) = spec[:8]
    opts = spec[8] if len(spec) > 8 else {}
    ux, uy = unit(ang)
    under = opts.get("under", False)
    leaf = leaf_shape(L, seed, narrow=opts.get("narrow", 1.0), bend=opts.get("bend"),
                      sway=opts.get("sway", 0.0))
    # petiole: a smooth cubic from the soil (rising nearly vertically) that
    # arrives aligned with the leaf axis, ending tucked under the blade base
    S = (sx, RIM_Y + 14)
    E = (bx + ux * 8, by + uy * 8)
    h = by - S[1]
    lean = opts.get("lean", 0.0)
    c1 = (S[0] + lean + bow, S[1] + h * opts.get("k1", 0.45))
    k2 = abs(h) * opts.get("k2", 0.42)
    c2 = (bx - ux * k2, by - uy * k2)
    pts = []
    for i in range(9):
        t = i / 8
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * S[0] + b * c1[0] + c * c2[0] + d * E[0],
                    a * S[1] + b * c1[1] + c * c2[1] + d * E[1]))
    plen = abs(h)
    w0 = 5.2 + L * 0.012
    w1 = 2.6 + L * 0.008
    pc, pv = PET[layer]
    out = [stem(pts, w0, w1, pc)]
    # pulvinus: short swollen joint just below the blade (round-capped). It ends
    # just short of the blade base, its round cap wholly on the petiole side, so it
    # never straddles the blade edge (the rounded base otherwise covered half its end
    # and the pale joint seemed to run on into the midrib)
    pw = w1 + 1.8
    gap = pw / 2 + 1.2
    pa = (bx - ux * (11 + gap), by - uy * (11 + gap))
    pb = (bx - ux * gap, by - uy * gap)
    out.append(line([pa, pb], pw, pv))
    if under:
        # burgundy underside: flat halves + rose midrib only
        fill, shade = UNDER
        extra = lambda lf: midrib(lf, P["rose"])  # noqa: E731
    else:
        fill, shade = TONE[layer]
        extra = lambda lf: stripes(lf, seed) + midrib(lf, MIDRIB)  # noqa: E731
    side = "l" if ang > 0 else "r"
    g = leaf_g(leaf, fill, shade=shade, side=side, extra=extra,
               transform=T(bx, by, ang))
    out.append(g)
    return "".join(out), plen


# (soil x, base x, base y, angle, length, layer, seed, bow, opts)
# bend/sway curve each midrib (bend toward the ground on the leaning blades so
# their tips droop); lean/bow arc the petioles outward, more on the outer ones.
LEAVES = [
    # back layer (night)
    (296, 254, 290, -14, 224, "back", 1, 0, {"lean": 26, "k1": 0.55, "bend": -0.05, "sway": 0.1}),
    (312, 376, 288, 29, 200, "back", 2, 0, {"lean": -16, "k1": 0.55, "bend": 0.07}),
    # middle layer (deep)
    (286, 180, 358, -51, 168, "mid", 3, -8, {"lean": -8, "bend": -0.12, "k2": 0.5}),
    (322, 422, 404, 66, 140, "back", 4, 10, {"lean": 22, "bend": 0.15, "k2": 0.5, "narrow": 0.9}),
    (302, 330, 368, 9, 148, "mid", 5, 0, {"under": True, "narrow": 0.72, "lean": -2, "bend": 0.06}),
    # front layer (forest)
    (282, 196, 474, -78, 132, "front", 6, -6, {"lean": -10, "bend": -0.16, "k2": 0.55}),
    (298, 252, 434, -28, 120, "front", 8, 0, {"under": True, "narrow": 0.76, "bend": -0.07}),
    (306, 370, 452, 41, 150, "front", 7, 4, {"lean": -2, "bend": 0.1, "sway": -0.08, "narrow": 0.86}),
]

FURLED = (298, 290, 398, -3, 108)


def furled(sx, bx, by, ang, L):
    """A new leaf still rolled into a slim spike on its own petiole."""
    ux, uy = unit(ang)
    S = (sx, RIM_Y + 14)
    pts = [S, (sx + (bx - sx) * 0.4, S[1] - (S[1] - by) * 0.5), (bx, by)]
    out = [stem(pts + [(bx + ux * 10, by + uy * 10)], 4.6, 3.4, P["sage"])]
    lf = Leaf(L, [(0.08, 0.05), (0.3, 0.085), (0.62, 0.075), (0.88, 0.04)],
              [(0.08, 0.05), (0.3, 0.08), (0.62, 0.07), (0.88, 0.035)], bend=0.06)
    def wrap(leaf):  # the rolled edge: one lighter spiral band
        a = [leaf.pt(t, -0.07 + 0.14 * t) for t in (0.05, 0.3, 0.6, 0.9)]
        b = [leaf.pt(t, 0.02 + 0.03 * t) for t in (0.9, 0.6, 0.3, 0.05)]
        return f'<path d="{cr_path(a + b, closed=True, sharp={0, 3, 4, 7})}" fill="{P["forest"]}"/>'
    out.append(leaf_g(lf, P["mid"], extra=wrap, transform=T(bx, by, ang)))
    return "".join(out)


def build():
    reset_ids()
    back, front = pot(kind="classic", cx=CX, rim_y=RIM_Y, rx=RX, base_w=72, band=True)
    parts = [back]
    for i, spec in enumerate(LEAVES):
        if i == 5:
            parts.append(furled(*FURLED))
        g, _ = plant_leaf(spec)
        parts.append(g)
    parts.append(front)
    return "\n".join(parts)


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(HERE), "out", "calathea_ornata.svg")
    with open(out, "w") as fh:
        fh.write(svg_doc(build(), "Calathea ornata (pinstripe calathea)"))
    print(out, os.path.getsize(out))
