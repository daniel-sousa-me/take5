"""Tradescantia zebrina (inch plant / wandering dude) -- v4 generator.

A low, wide mound of jointed succulent plum stems. Ovate pointed leaves sit
alternately at swollen nodes, their rounded bases clasping the stem. Upper
surface: two broad silver stripes either side of a dark purple-green centre
band, dark green margins. Some leaves are turned to show the plum underside.
Strands trail over the rim (long right, medium left, short front-left) with
their leaves turning up; two tiny three-petalled blush flowers sit at shoot tips.

Leaves are drawn once per (shape, tone) as templates in <defs> (unit length
100, shaded half on local +x) and placed with <use>; flipping keeps the shaded
half on the world-right side, as in the rest of the set.
"""
import math
import re
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core import PAL, cr_path, cr_sample, ribbon, f, pot, svg_doc, reset_ids  # noqa: E402

P = PAL
SOIL_Y = 606
LS = 1.12  # crown leaf scale

# ---------------------------------------------------------------- tones
# upper-surface tiers: margin lit/shade, centre band lit/shade, silver lit/shade
TIERS = {
    0: ("#2A342E", "#222B26", "#3E2E37", "#33262E", "#97A393", "#818D7F"),
    1: ("#2F4435", "#26362B", "#4B3440", "#3E2B35", "#B7C0AC", "#9CA695"),
    2: ("#3D5540", "#324636", P["wine"], "#4E3036", "#DCDDCD", "#C2C8B5"),
}
# undersides: lit, shade, midrib
UNDER = {
    0: (P["burgundy"], P["wine"], P["rose"]),
    1: (P["plum"], P["burgundy"], P["blush"]),
}
STEM = {0: P["burgundy"], 1: P["plum"], 2: "#9A636A"}
COLLAR = {0: P["wine"], 1: P["burgundy"], 2: P["plum"]}

# ---------------------------------------------------------------- leaf template
# half-width profile (t along axis from node 0 -> tip 1, w as fraction of length)
PROF = [(-0.06, 0.0), (-0.045, 0.075), (0.0, 0.14), (0.08, 0.205), (0.2, 0.25),
        (0.34, 0.262), (0.48, 0.243), (0.62, 0.195), (0.76, 0.13), (0.88, 0.062),
        (0.95, 0.024), (1.0, 0.0)]
SHAPES = {  # name: (width scale, tip curl)
    "a": (1.0, 0.0),
    "b": (0.9, 0.07),
    "c": (1.08, -0.05),
}


def hw(t):
    for (t0, w0), (t1, w1) in zip(PROF, PROF[1:]):
        if t0 <= t <= t1:
            return w0 + (w1 - w0) * (t - t0) / ((t1 - t0) or 1)
    return 0.0


class Tmpl:
    def __init__(self, wide, curl):
        self.wide, self.curl = wide, curl

    def p(self, t, x):
        """axis t, signed fraction x of half-width -> template units (L=100)."""
        tt = max(0.0, t)
        return ((x * hw(t) * self.wide + self.curl * tt * tt) * 100, -t * 100)

    def outline(self):
        ts = [t for t, _ in PROF]
        right = [self.p(t, 1) for t in ts[1:-1]]
        left = [self.p(t, -1) for t in ts[1:-1]][::-1]
        pts = [self.p(ts[0], 0)] + right + [self.p(1.0, 0)] + left
        return cr_path(pts, closed=True, sharp={len(right) + 1})

    def half(self, side):
        ts = [t for t, _ in PROF]
        edge = [self.p(t, side) for t in ts[1:-1]]
        pts = [self.p(ts[0], 0)] + edge + [self.p(1.0, 0)]
        d = cr_path(pts, closed=False)
        mid = [self.p(t, 0) for t in (0.75, 0.5, 0.25)]
        return d + "".join(f"L{f(x)} {f(y)}" for x, y in mid) + "Z"

    def region(self, side, t0, t1, lo, hi, taper0=0.12, taper1=0.25, jit=None):
        """strip between fractions lo..hi of the half-width, tapering at both ends."""
        n = 8
        outer, inner = [], []
        for i in range(1, n):
            t = t0 + (t1 - t0) * i / n
            env = min(1.0, (t - t0) / taper0, (t1 - t) / taper1) ** 0.6
            c, h = (lo + hi) / 2, (hi - lo) / 2 * env
            j = jit[i] if jit else 0
            outer.append(self.p(t, side * (c + h + j)))
            inner.append(self.p(t, side * (c - h + j * 0.4)))
        a = self.p(t0, side * lo)
        b = self.p(t1, side * (lo + hi) / 2)
        ring = [a] + outer + [b] + inner[::-1]
        return cr_path(ring, closed=True, sharp={0, len(outer) + 1})

    def band(self, side, frac=0.3):
        ts = [0.02, 0.14, 0.3, 0.46, 0.62, 0.78, 0.9]
        edge = [self.p(t, side * frac) for t in ts]
        pts = [self.p(-0.04, 0)] + edge + [self.p(0.985, 0)]
        d = cr_path(pts, closed=False)
        return d + "".join(f"L{f(x)} {f(y)}" for x, y in [self.p(t, 0) for t in (0.6, 0.3)]) + "Z"

    def line(self, x, t0, t1, n=6):
        pts = [self.p(t0 + (t1 - t0) * i / n, x) for i in range(n + 1)]
        return "M" + "L".join(f"{f(a)} {f(b)}" for a, b in pts)


def tmpl_upper(tid, shape, tier, seed):
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    mg, mgs, bd, bds, sv, svs = TIERS[tier]
    rnd = random.Random(seed)
    g = [f'<g id="{tid}"><path d="{lf.outline()}" fill="{mg}"/>',
         f'<path d="{lf.half(1)}" fill="{mgs}"/>']
    for side, col in ((-1, sv), (1, svs)):
        jit = [rnd.uniform(-0.035, 0.035) for _ in range(9)]
        g.append(f'<path d="{lf.region(side, 0.03, 0.88, 0.24, 0.7, jit=jit)}" fill="{col}"/>')
    g.append(f'<path d="{lf.band(-1)}" fill="{bd}"/><path d="{lf.band(1)}" fill="{bds}"/>')
    # fine parallel venation inside the silver (longitudinal, low contrast)
    vl = "".join(lf.line(s * 0.52, 0.1, 0.8) for s in (-1, 1))
    g.append(f'<path d="{vl}" fill="none" stroke="{bds}" stroke-width="1.5" '
             f'stroke-linecap="round" opacity=".22"/>')
    g.append(f'<path d="{lf.line(0, 0.0, 0.9)}" fill="none" stroke="{sv}" stroke-width="2" '
             f'stroke-linecap="round" opacity=".4"/></g>')
    return "".join(g)


def tmpl_under(tid, shape, tone):
    wide, curl = SHAPES[shape]
    lf = Tmpl(wide, curl)
    lit, shd, mid = UNDER[tone]
    vl = "".join(lf.line(s * 0.5, 0.08, 0.82) for s in (-1, 1))
    return (f'<g id="{tid}"><path d="{lf.outline()}" fill="{lit}"/>'
            f'<path d="{lf.half(1)}" fill="{shd}"/>'
            f'<path d="{vl}" fill="none" stroke="{shd}" stroke-width="1.5" stroke-linecap="round" opacity=".35"/>'
            f'<path d="{lf.line(0, 0.0, 0.9)}" fill="none" stroke="{mid}" stroke-width="2.2" '
            f'stroke-linecap="round" opacity=".55"/></g>')


def _ints(svg):
    """template coords are in 1/100 leaf units: integers are plenty."""
    return re.sub(r'd="[^"]*"', lambda d: re.sub(r"-?\d+\.\d+", lambda m: str(round(float(m.group()))),
                                                 d.group()), svg)


def defs():
    out = ["<defs>"]
    k = 0
    for tier in TIERS:
        for s in SHAPES:
            if tier == 0 and s == "c":  # back tier only needs two shapes
                continue
            k += 1
            out.append(tmpl_upper(f"z{tier}{s}", s, tier, k))
    for tone in UNDER:
        for s in ("a", "b"):
            out.append(tmpl_under(f"u{tone}{s}", s, tone))
    out.append("</defs>")
    return _ints("".join(out))


def place(tid, x, y, rot, L, wide=1.0):
    """shaded half (+x local) must face world right; flip when it would not."""
    flip = math.cos(math.radians(rot)) < 0
    sx = (-1 if flip else 1) * wide * L / 100
    return (f'<use href="#{tid}" transform="translate({f(x)} {f(y)}) rotate({f(rot)}) '
            f'scale({sx:.3f} {L / 100:.3f})"/>')


# ---------------------------------------------------------------- flower
def flower(x, y, r, rot=0):
    """Three broad petals (blush), rose eye, cream anthers; tiny."""
    out = [f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)})">']
    tones = ("#E8BDB8", P["blush"], "#E0AFAB")
    pd = cr_path([(0, 0), (r * 0.5, -r * 0.3), (r * 0.56, -r * 0.72), (r * 0.26, -r * 1.02), (0, -r * 1.12),
                  (-r * 0.26, -r * 1.02), (-r * 0.56, -r * 0.72), (-r * 0.5, -r * 0.3)], closed=True, sharp={0, 4})
    for i in range(3):
        out.append(f'<path d="{pd}" fill="{tones[i]}" transform="rotate({i * 120})"/>')
    out.append(f'<circle r="{f(r * 0.27)}" fill="{P["rose"]}"/>')
    for i in range(3):
        a = math.radians(i * 120 + 60)
        out.append(f'<circle cx="{f(math.sin(a) * r * 0.3)}" cy="{f(-math.cos(a) * r * 0.3)}" '
                   f'r="{f(r * 0.11)}" fill="{P["ivory"]}"/>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- shoots
def unit(v):
    m = math.hypot(*v) or 1
    return (v[0] / m, v[1] / m)


def rot_of(u):
    return math.degrees(math.atan2(u[0], -u[1]))


def along(s, frac):
    d = [0.0]
    for p, q in zip(s, s[1:]):
        d.append(d[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
    tgt = frac * d[-1]
    for i in range(1, len(s)):
        if d[i] >= tgt:
            u = (tgt - d[i - 1]) / ((d[i] - d[i - 1]) or 1)
            p = (s[i - 1][0] + (s[i][0] - s[i - 1][0]) * u, s[i - 1][1] + (s[i][1] - s[i - 1][1]) * u)
            return p, unit((s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1])), d[-1]
    return s[-1], unit((s[-1][0] - s[-2][0], s[-1][1] - s[-2][1])), d[-1]


def arc(x0, a0, a1, S, n=6, y0=SOIL_Y):
    """stem path from the soil: heading (deg from vertical, + right) a0 -> a1."""
    pts = [(x0, y0)]
    x, y = x0, y0
    k = 24
    for i in range(1, k + 1):
        a = math.radians(a0 + (a1 - a0) * (i - 0.5) / k)
        x += math.sin(a) * S / k
        y -= math.cos(a) * S / k
        if i % (k // n) == 0:
            pts.append((x, y))
    return pts


def shoot(pts, w0, w1, st, nodes, leaf_tier=None):
    """nodes: (frac, side, L, tid, ang, up). `ang` turns the leaf away from the
    stem tangent to its side (deg); `up` blends the direction toward vertical."""
    s = cr_sample(pts, 10)
    total = along(s, 1.0)[2]
    stems = [f'<path d="{ribbon(pts, w0, w1, per=4)}" fill="{STEM[st]}"/>']
    leaves, collars = [], []
    for fr, side, L, tid, ang, up in nodes:
        p, t, _ = along(s, fr)
        ww = w0 + (w1 - w0) * fr
        # tubular sheath above the node: a short, fatter, darker collar
        f1 = min(1.0, fr + 8 / total)
        if f1 - fr > 0.004 and fr < 0.995:
            q, _, _ = along(s, f1)
            collars.append((f"M{f(p[0])} {f(p[1])}l{f(q[0] - p[0])} {f(q[1] - p[1])}", ww * 1.4))
        a = math.radians(ang * side)
        dx = t[0] * math.cos(a) - t[1] * math.sin(a)
        dy = t[0] * math.sin(a) + t[1] * math.cos(a)
        u = unit((dx, dy - up))
        # leaf base sits a hair past the node so the clasping base wraps it
        leaves.append(place(tid, p[0], p[1], rot_of(u), L))
    if collars:
        cw = sum(w for _, w in collars) / len(collars)
        stems.append(f'<path d="{"".join(d for d, _ in collars)}" stroke="{COLLAR[st]}" stroke-width="{f(cw)}"/>')
    return "".join(stems), "".join(leaves), s


def auto_nodes(n, L0, tier, first, f0=0.26, shrink=0.78, ang=52, up=0.25, under=(), shapes="abcab",
               seed=0, tip_ang=12):
    rnd = random.Random(seed)
    out = []
    side = first
    for i in range(n):
        fr = 1.0 if i == n - 1 else f0 + (1 - f0) * i / (n - 1) + rnd.uniform(-0.03, 0.03)
        L = L0 * (1 - (1 - shrink) * i / max(1, n - 1)) * rnd.uniform(0.88, 1.1)
        a = tip_ang if i == n - 1 else ang * rnd.uniform(0.7, 1.3)
        uu = up * rnd.uniform(0.6, 1.5)
        shp = shapes[i % len(shapes)]
        if tier == 0 and shp == "c":
            shp = "b"
        tid = (f"u{under[1]}{'a' if shp == 'c' else shp}" if i in under[0] else f"z{tier}{shp}") \
            if under else f"z{tier}{shp}"
        out.append((fr, side, L, tid, a, uu))
        side = -side
    return out


# ---------------------------------------------------------------- plant
def build():
    back, front = pot("classic", cx=300, rim_y=590, rx=102, base_w=72, band=True)
    out = [defs(), back]

    # crown shoots: (x0, a0, a1, S, stem tier, leaf tier, n, L0, first side, extras)
    crown = [
        # back tier: tall centre and shoulders (darkest)
        (298, -2, -12, 276, 0, 0, 7, 72, 1, dict(seed=1, under=({3}, 0), f0=0.22)),
        (306, 12, 30, 272, 0, 0, 7, 72, -1, dict(seed=2, f0=0.22)),
        (292, -20, -46, 248, 0, 0, 7, 72, -1, dict(seed=3, f0=0.22)),
        (312, 32, 62, 236, 0, 0, 7, 70, 1, dict(seed=4, under=({2}, 0), f0=0.22)),
        (288, -40, -76, 214, 0, 0, 6, 70, 1, dict(seed=12, f0=0.22)),
        (310, 46, 84, 206, 0, 0, 6, 68, -1, dict(seed=16, f0=0.22)),
        # middle tier
        (284, -48, -104, 178, 1, 1, 6, 66, -1, dict(seed=5, up=0.5)),
        (318, 50, 104, 174, 1, 1, 6, 66, 1, dict(seed=6, up=0.5, under=({3}, 1))),
        (296, -10, -24, 220, 1, 1, 5, 70, 1, dict(seed=7)),
        (306, 20, 40, 210, 1, 1, 5, 68, -1, dict(seed=8)),
        (292, -32, -54, 200, 1, 1, 5, 68, 1, dict(seed=13)),
        # front tier: low over the rim
        (288, -68, -124, 132, 2, 2, 5, 62, -1, dict(seed=9, up=0.7)),
        (314, 70, 124, 128, 2, 2, 5, 62, 1, dict(seed=10, up=0.7)),
        (304, 30, 56, 150, 2, 2, 4, 62, -1, dict(seed=14)),
        (296, -36, -60, 150, 2, 2, 4, 62, 1, dict(seed=15)),
        (300, -6, 8, 140, 2, 2, 4, 64, 1, dict(seed=11, up=0.1)),
        # two low leaves right at the rim, hiding the stem bases
        (290, -6, -40, 64, 2, 2, 2, 56, -1, dict(seed=17, f0=0.6, ang=40, up=0.2, tip_ang=40)),
        (314, 14, 52, 56, 2, 2, 2, 54, 1, dict(seed=18, f0=0.6, ang=40, up=0.2, tip_ang=40)),
    ]
    tips = {}
    for i, (x0, a0, a1, S, st, lt, n, L0, first, ex) in enumerate(crown):
        # lift the dome (upright shoots longer), keep the sides within the card
        tall = abs(a1) < 60 and S > 100
        S *= 1.2 if tall else 0.9
        n += 1 if tall and S > 240 else 0
        L0 *= LS
        x0 = 300 + (x0 - 300) * 0.4 + max(-56, min(56, a0 * 0.8))  # spread over the soil
        pts = arc(x0, a0, a1, S)
        w0 = 7.2 - st * 0.6
        nodes = auto_nodes(n, L0, lt, first, **ex)
        s, l, samp = shoot(pts, w0, w0 * 0.62, st, nodes)
        out += [s, l]
        tips[i] = samp

    # flowers nestled at two shoot tips
    out.append(flower(*along(tips[15], 0.93)[0], 13, 20))
    out.append(flower(*along(tips[7], 0.9)[0], 12, -15))

    out.append(front)

    # trailing strands over the rim (drawn in front of the pot)
    trails = [
        # long right strand
        ([(352, 596), (392, 588), (428, 598), (458, 632), (476, 684), (486, 730), (490, 768)],
         5.2, 3.2, 1, [
             (0.12, 1, 50, "z2a", 64, 0.5), (0.27, -1, 46, "z1b", 70, 0.8),
             (0.42, 1, 44, "u1a", 74, 0.9), (0.56, -1, 42, "z2c", 78, 1.0),
             (0.70, 1, 40, "z1a", 78, 1.1), (0.84, -1, 38, "z2b", 80, 1.2),
             (1.0, 1, 34, "z1a", 70, 1.8)]),
        # medium left strand
        ([(250, 596), (212, 590), (180, 600), (156, 632), (142, 676), (134, 712)],
         5.0, 3.2, 1, [
             (0.14, -1, 48, "z2c", 64, 0.5), (0.33, 1, 44, "z1a", 72, 0.8),
             (0.52, -1, 42, "z2a", 78, 1.0), (0.7, 1, 40, "u1b", 80, 1.0),
             (0.86, -1, 38, "z1b", 80, 1.2), (1.0, 1, 34, "z2a", 66, 1.8)]),
        # short centre-front drape
        ([(334, 597), (348, 606), (356, 626), (358, 652)],
         4.4, 3.2, 2, [
             (0.6, 1, 40, "z1b", 64, 0.3), (1.0, -1, 36, "z2c", 50, 1.4)]),
        # short strand over the front-left of the rim
        ([(276, 597), (254, 614), (242, 640), (240, 668)],
         4.4, 3.0, 2, [
             (0.35, -1, 42, "z2b", 80, 0.9), (0.68, 1, 38, "z1c", 80, 1.1),
             (1.0, -1, 34, "z2a", 60, 1.8)]),
    ]
    ts, tl = [], []
    for pts, w0, w1, st, nodes in trails:
        s, l, _ = shoot(pts, w0, w1, st, nodes)
        ts.append(s)
        tl.append(l)
    out += ts + tl
    return "".join(out)


if __name__ == "__main__":
    reset_ids()
    here = os.path.dirname(os.path.abspath(__file__))
    dst = os.path.join(here, "..", "out", "tradescantia_zebrina.svg")
    open(dst, "w").write(svg_doc(build(), "Tradescantia zebrina (inch plant)"))
    print("wrote", os.path.normpath(dst), os.path.getsize(dst), "bytes")
